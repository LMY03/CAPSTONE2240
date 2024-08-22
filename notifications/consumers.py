import json
from channels.generic.websocket import WebsocketConsumer

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        data = json.loads(text_data)
        self.send(text_data=json.dumps({
            'message': data['message']
        }))

    def task_complete(self, event):
        self.send(text_data=json.dumps({
            'issue_name': event['issue_name'],
            'status': event['status'],
            'folder_id': event.get('folder_id')
        }))
