from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import Optional
from datetime import datetime
from app.models import TransactionInput, TransactionUpdate, TransactionBatchInput
from app.database import engine_tools
from app.services import image_service

router = APIRouter()

@router.get("/transactions")
async def get_transactions(
    user_id: Optional[int] = None, 
    page: int = 1, 
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = 'dateOut',
    sort_order: str = 'desc',
    search_term: Optional[str] = None,
    status: Optional[str] = None
):
    offset = (page - 1) * limit
    with engine_tools.connect() as conn:
        conditions = []
        params = {}
        
        if user_id is not None:
            conditions.append("t.user_id = :user_id")
            params["user_id"] = user_id
            
        if start_date:
            conditions.append("t.checkout_timestamp >= :start_date")
            params["start_date"] = start_date
            
        if end_date:
            conditions.append("t.checkout_timestamp < DATE_ADD(:end_date, INTERVAL 1 DAY)")
            params["end_date"] = end_date

        if status:
            status_list = status.split(',')
            status_conditions = []
            for s in status_list:
                s = s.strip()
                if s == 'Returned':
                    status_conditions.append("t.return_timestamp IS NOT NULL")
                elif s == 'Overdue':
                    status_conditions.append("(t.return_timestamp IS NULL AND t.desired_return_date < NOW())")
                elif s == 'Borrowed':
                    status_conditions.append("(t.return_timestamp IS NULL AND (t.desired_return_date >= NOW() OR t.desired_return_date IS NULL))")
            
            if status_conditions:
                conditions.append(f"({' OR '.join(status_conditions)})")

        if search_term:
            conditions.append("(CAST(t.user_id AS CHAR) LIKE :search OR CAST(t.tool_id AS CHAR) LIKE :search OR LOWER(t.purpose) LIKE :search)")
            params["search"] = f"%{search_term.lower()}%"

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        order_clause = "ORDER BY t.checkout_timestamp DESC"
        if sort_by == 'dateOut':
            order_clause = f"ORDER BY t.checkout_timestamp {sort_order.upper()}"
        elif sort_by == 'dateDue':
            order_clause = f"ORDER BY t.desired_return_date {sort_order.upper()}"

        count_sql = f"""
            SELECT COUNT(*) 
            FROM transactions t 
            LEFT JOIN users u ON t.user_id = u.user_id
            LEFT JOIN tools tl ON t.tool_id = tl.tool_id
            {where_clause}
        """
        total = conn.execute(text(count_sql), params).scalar()

        base_sql = f"""
            SELECT t.transaction_id, t.user_id, t.tool_id, t.checkout_timestamp, 
                   t.desired_return_date, t.return_timestamp, t.quantity, t.purpose, 
                   t.image_path, t.classification_correct, t.weight,
                   u.user_name, tl.tool_name
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
            LEFT JOIN tools tl ON t.tool_id = tl.tool_id
            {where_clause}
            {order_clause}
        """
        
        if limit > 0:
            base_sql += " LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
        result = conn.execute(text(base_sql), params)
        
        transactions = []
        for row in result:
            status = "Borrowed"
            if row.return_timestamp:
                status = "Returned"
            elif row.desired_return_date and row.desired_return_date < datetime.now():
                status = "Overdue"
            
            transactions.append({
                "transaction_id": row.transaction_id,
                "user_id": row.user_id,
                "user_name": row.user_name,
                "tool_id": row.tool_id,
                "tool_name": row.tool_name,
                "checkout_timestamp": row.checkout_timestamp,
                "desired_return_date": row.desired_return_date,
                "return_timestamp": row.return_timestamp,
                "quantity": row.quantity,
                "purpose": row.purpose,
                "status": status
            })
            
        return {
            "items": transactions,
            "total": total,
            "page": page,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

@router.post("/transactions")
async def create_transaction(transaction: TransactionInput):
    with engine_tools.connect() as conn:
        _process_single_transaction(conn, transaction)
        conn.commit()

    return {"success": True, "message": "Transaction created successfully"}

@router.post("/transactions/batch")
async def create_transaction_batch(batch: TransactionBatchInput):
    """
    Creates multiple transactions in one atomic operation.
    If any transaction fails, the entire batch is rolled back.
    """
    with engine_tools.begin() as conn: # 'begin()' starts a transaction
        count = 0
        for transaction in batch.transactions:
            try:
                _process_single_transaction(conn, transaction)
                count += 1
            except Exception as e:
                # SQLAlchemy's context manager will auto-rollback on exception
                print(f"[SERVER] Batch Error on item {count}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to process item {count+1}: {str(e)}")
    
    return {"success": True, "message": f"Successfully created {count} transactions"}

def _process_single_transaction(conn, transaction: TransactionInput):
    """Helper to process logic for a single transaction inside an existing connection"""
    
    # --- Handle Image Move Logic ---
    if transaction.image_path:
        # We need the tool name to organize folders
        # Note: image moving is not transactional on the filesystem, 
        # but if DB fails, we just have an orphan file (better than missing file)
        if transaction.tool_id:
              tool_row = conn.execute(text("SELECT tool_name FROM tools WHERE tool_id = :id"), {"id": transaction.tool_id}).fetchone()
              if tool_row:
                  tool_name = tool_row[0]
                  is_correct = transaction.classification_correct if transaction.classification_correct is not None else False
                  
                  new_path = image_service.move_image_to_permanent(transaction.image_path, tool_name, is_correct)
                  
                  if new_path:
                      print(f"[SERVER] Moved image to {new_path}")
                      transaction.image_path = new_path
                  else:
                      print(f"[SERVER] Warning: Image path provided {transaction.image_path} but file not found in temp.")

    query = text("""
        INSERT INTO transactions
        (user_id, tool_id, desired_return_date, return_timestamp, quantity, purpose,
            image_path, classification_correct, weight)
        VALUES
        (:user_id, :tool_id, :desired_return_date, :return_timestamp, :quantity, :purpose,
            :image_path, :classification_correct, :weight)
    """)
    conn.execute(query, {
        "user_id": transaction.user_id,
        "tool_id": transaction.tool_id,
        "desired_return_date": transaction.desired_return_date,
        "return_timestamp": transaction.return_timestamp,
        "quantity": transaction.quantity,
        "purpose": transaction.purpose,
        "image_path": transaction.image_path,
        "classification_correct": transaction.classification_correct,
        "weight": transaction.weight,
    })

@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int):
    with engine_tools.connect() as conn:
        check = conn.execute(
            text("SELECT transaction_id FROM transactions WHERE transaction_id = :id"),
            {"id": transaction_id},
        ).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Transaction not found")

        conn.execute(
            text("DELETE FROM transactions WHERE transaction_id = :id"),
            {"id": transaction_id},
        )
        conn.commit()

    return {"success": True, "message": "Transaction deleted successfully"}

@router.put("/transactions/{transaction_id}")
async def update_transaction(transaction_id: int, transaction: TransactionUpdate):
    with engine_tools.connect() as conn:
        check = conn.execute(
            text("SELECT transaction_id FROM transactions WHERE transaction_id = :id"),
            {"id": transaction_id},
        ).fetchone()
        if not check:
            raise HTTPException(status_code=404, detail="Transaction not found")

        updates = []
        params = {"id": transaction_id}

        if transaction.user_id is not None:
            updates.append("user_id = :user_id")
            params["user_id"] = transaction.user_id
        if transaction.tool_id is not None:
            updates.append("tool_id = :tool_id")
            params["tool_id"] = transaction.tool_id
        if transaction.desired_return_date is not None:
            updates.append("desired_return_date = :desired_return_date")
            params["desired_return_date"] = transaction.desired_return_date
        if transaction.return_timestamp is not None:
            updates.append("return_timestamp = :return_timestamp")
            params["return_timestamp"] = transaction.return_timestamp
        if transaction.quantity is not None:
            updates.append("quantity = :quantity")
            params["quantity"] = transaction.quantity
        if transaction.purpose is not None:
            updates.append("purpose = :purpose")
            params["purpose"] = transaction.purpose
        if transaction.image_path is not None:
            updates.append("image_path = :image_path")
            params["image_path"] = transaction.image_path
        if transaction.classification_correct is not None:
            updates.append("classification_correct = :classification_correct")
            params["classification_correct"] = transaction.classification_correct
        if transaction.weight is not None:
            updates.append("weight = :weight")
            params["weight"] = transaction.weight

        if not updates:
            return {"success": True, "message": "No changes provided"}

        sql = f"UPDATE transactions SET {', '.join(updates)} WHERE transaction_id = :id"
        conn.execute(text(sql), params)
        conn.commit()

    return {"success": True, "message": "Transaction updated successfully"}
