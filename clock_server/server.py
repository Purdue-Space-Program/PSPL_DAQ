from flask import Flask, jsonify, render_template
import synnax as sy
import threading
import time

sy_client = sy.Synnax(
    host='10.165.89.106',
    port=2701,
    username='Bill',
    password='Bill',
    secure=False,
)

clock_string_ch = sy_client.channels.retrieve('T_CLOCK_STRING')

app = Flask(__name__)

latest_data = {'T_CLOCK_STRING': 'Initializing...'}
data_lock = threading.Lock()

def stream_updater():
    """
    Function to run in a separate thread.
    It constantly polls the Synnax streamer and updates the latest_data dictionary.
    """
    print("Stream updater thread started.")
    with sy_client.open_streamer([clock_string_ch.key]) as streamer:
        for frame in streamer:
            for v in frame[clock_string_ch.key]:
                print(v)
                with data_lock:
                    latest_data['T_CLOCK_STRING'] = v 

# Start the stream updater thread when the application starts
updater_thread = threading.Thread(target=stream_updater, daemon=True)
updater_thread.start()

# --- Flask Routes ---

@app.route('/')
def index():
    """
    This function serves the main HTML page.
    """
    return render_template('index.html')


@app.route('/api/string', methods=['GET'])
def get_string():
    """
    This function handles GET requests to fetch the current string.
    It reads the pre-updated value from the shared storage.
    """
    # --- CRITICAL SECTION START ---
    # Acquire the lock to safely read the latest value
    with data_lock:
        string_value = latest_data['T_CLOCK_STRING']
    # --- CRITICAL SECTION END ---
    
    return jsonify(current_string=string_value)


if __name__ == '__main__':
    # Run the app.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False) 
    # NOTE: Set use_reloader=False when using threading with debug=True 
    # to prevent the thread from being started twice.
