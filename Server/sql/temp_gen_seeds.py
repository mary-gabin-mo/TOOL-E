import random
from datetime import datetime, timedelta

users = [101, 102, 103, 104, 105]
tools = list(range(1, 16))
purposes = ['Personal Project', 'Academic Course']

with open('transactions_seed.sql', 'w', encoding='utf-8') as f:
    f.write("USE `tool_e_db`;\n\n")
    f.write("INSERT INTO `transactions`\n")
    f.write("(`user_id`, `tool_id`, `checkout_timestamp`, `desired_return_date`, `return_timestamp`, `quantity`, `purpose`, `image_path`, `classification_correct`, `weight`)\n")
    f.write("VALUES\n")

    values = []
    base_date = datetime.now()
    count = 500

    for i in range(count):
        uid = random.choice(users)
        tid = random.choice(tools)
        
        # Checkout between 60 days ago and today
        days_ago = random.randint(0, 60)
        checkout = base_date - timedelta(days=days_ago)
        checkout_s = checkout.strftime('%Y-%m-%d %H:%M:%S')
        
        # Desired return 1-14 days after checkout
        duration = random.randint(1, 14)
        desired = checkout + timedelta(days=duration)
        desired_s = desired.strftime('%Y-%m-%d %H:%M:%S')
        
        # Return date:
        if random.random() < 0.8:
            ret_duration = random.randint(0, duration + 5)
            ret_date = checkout + timedelta(days=ret_duration)
            if ret_date > base_date:
                 ret_s = "NULL" 
            else:
                 ret_s = f"'{ret_date.strftime('%Y-%m-%d %H:%M:%S')}'"
        else:
            ret_s = "NULL"
            
        purp = random.choice(purposes)
        img = f"uploads/mock_tool_{tid}.jpg"
        
        is_last = (i == count - 1)
        terminator = ";" if is_last else ","
        
        val_str = f"({uid}, {tid}, '{checkout_s}', '{desired_s}', {ret_s}, 1, '{purp}', '{img}', 1, 0){terminator}\n"
        f.write(val_str)

print("Check 'transactions_seed.sql' for the generated SQL.")
