import time
import json
import random
import os
import sys
from dotenv import load_dotenv
from kafka import KafkaProducer

# 1. Setup path to find project root if executed from inside container
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# 2. Load environment
load_dotenv(os.path.join(project_root, '.env'))

BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'device_data')

def json_serializer(data):
	return json.dumps(data).encode('utf-8')

def main():
	print('Starting SCM Data Producer...')
	print('Connecting to Kafka:', BOOTSTRAP_SERVERS)

	# Create Producer
	try:
		producer = KafkaProducer(
			bootstrap_servers=BOOTSTRAP_SERVERS,
			value_serializer=json_serializer,
			linger_ms=10
		)
		print(f'Connected! Sending real-time data to "{KAFKA_TOPIC}"')
	except Exception as e:
		print('Connection Failed:', e)
		return

	routes = ['Newyork, USA', 'Chennai, India', 'Bengaluru, India', 'London, UK']

	try:
		while True:
			route_from = random.choice(routes)
			route_to = random.choice(routes)
			while route_from == route_to:
				route_to = random.choice(routes)

			data = {
				'Shipment_Number': f'SHP-{random.randint(1000,9999)}',
				'Device': f'IOT-{random.randint(1150,1158)}',
				'Temperature': round(random.uniform(10,40.0),1),
				'Battery': f"{round(random.uniform(2.00,5.00),2)}V",
				'Route_Details': f"{route_from} ➝ {route_to}",
			}

			try:
				producer.send(KAFKA_TOPIC, value=data)
				producer.flush()
				print(f"Sent: {data['Shipment_Number']} | {data['Device']} | {data['Route_Details']}")
			except Exception as e:
				print('Failed to send message:', e)

			time.sleep(int(os.getenv('PRODUCER_INTERVAL', '3')))

	except KeyboardInterrupt:
		print('\nProducer stopped by user')
	finally:
		try:
			producer.close()
		except Exception:
			pass


if __name__ == '__main__':
	main()
