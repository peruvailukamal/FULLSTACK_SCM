import json
import os
import time
from kafka import KafkaConsumer
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment from project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
load_dotenv(os.path.join(project_root, '.env'))
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017')
KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
TOPIC_NAME = os.getenv('KAFKA_TOPIC', 'device_data')
# Connect to MongoDB
try:
	mongo = MongoClient(MONGO_URI)
	db = mongo.get_database(os.getenv('DB_NAME', 'scm_db'))
	device_collection = db.get_collection('device_streams')
	print('Consumer successfully connected to MongoDB.')
except Exception as e:
	print(f'FATAL: Consumer error connecting to MongoDB. {e}')
	raise
print(f'Connecting to Kafka at {KAFKA_BOOTSTRAP}...')
consumer = None
for _ in range(30):
	try:
		consumer = KafkaConsumer(
			TOPIC_NAME,
			bootstrap_servers=KAFKA_BOOTSTRAP,
			auto_offset_reset='earliest',
			group_id='device-data-saver-group',
			value_deserializer=lambda m: json.loads(m.decode('utf-8'))
		)
		break
	except Exception as e:
		print('Waiting for Kafka broker...', e)
		time.sleep(2)
if consumer is None:
	print('Error connecting to Kafka: NoBrokersAvailable')
	raise SystemExit(1)
print('Kafka Consumer started. Listening for messages...')

try:
	for message in consumer:
		device_data = message.value
		print('Received:', device_data)
		# Map incoming message to DB document
		db_document = {
			'Shipment_Number': device_data.get('Shipment_Number'),
			'Device': device_data.get('Device'),
			'Temperature': device_data.get('Temperature'),
			'Battery': device_data.get('Battery'),
			'Route_Details': device_data.get('Route_Details'),
			'Received_At': datetime.now(timezone.utc)
		}
		try:
			result = device_collection.insert_one(db_document)
			print(f'Saved to DB with ID: {result.inserted_id}')
		except Exception as db_err:
			print('Error inserting into MongoDB:', db_err)

except KeyboardInterrupt:
	print('Stopping consumer.')
finally:
	try:
		consumer.close()
	except Exception:
		pass
	try:
		mongo.close()
	except Exception:
		pass
