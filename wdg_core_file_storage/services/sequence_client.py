
import httpx

class SequenceNumberingClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_templates(self, model_name):
        resp = httpx.get(f"{self.base_url}/templates/?code={model_name}")
        resp.raise_for_status()
        return resp.json()

    def create_template(self, data):
        resp = httpx.post(f"{self.base_url}/templates/", json=data)
        resp.raise_for_status()
        return resp.json()

    def delete_templates(self, model_name):
        resp = httpx.delete(f"{self.base_url}/templates/?code={model_name}")
        resp.raise_for_status()
        return resp.status_code == 204
