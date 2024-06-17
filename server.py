from flask import Flask, request
import threading

app = Flask(__name__)
signal_data = {"signal":None}

@app.route('/send_signal', methods=['POST'])
def send_signal():
	global signal_data
	signal = request.form.get('signal')
	if signal:
		signal_data['signal'] = signal
		return 'Signal received', 200
	else:
		return 'No signal', 400
	
@app.route('/get_signal', methods=['GET'])
def get_signal():
	global signal_data
	if signal_data['signal']:
		signal = signal_data['signal']
		signal_data['signal'] = None
		return signal, 200
	else:
		return 'No signal', 400
	
def run_server():
	app.run(host='0.0.0.0', port=5000)
	
if __name__ == '__main__':
	threading.Thread(target=run_server).start()
