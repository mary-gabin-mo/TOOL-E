import uvicorn
import os

if __name__ == "__main__":
    # Ensure we are running from the Server directory context
    # This allows relative imports inside app/ to work correctly if run from here
    
    # Run the uvicorn server
    # "app.main:app" refers to:
    #   app/       (folder)
    #   main.py    (file)
    #   app        (FasAPI instance variable inside main.py)
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)
