# This is the file you actually run to start the server: "python3 run.py".
#
# Why not just run app.py directly? Because models.py and the files under
# routes/ both do "from app import db" — that only works if app.py is always
# imported by its name "app", never run directly as the main script (Python
# treats "run directly" as a different, special case that breaks this).
# Keeping the real startup step in this tiny separate file sidesteps that.
from app import app

if __name__ == "__main__":
    app.run(debug=True)
