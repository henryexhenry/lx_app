import os
import json
from flask import Flask, send_from_directory
from crawling import LanXin_API, LanXin_service

app = Flask(__name__)
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

with open("credential.json") as f:
    credential = json.load(f)
username = credential.get("username")
password = credential.get("password")
base_url = credential.get("base_url")

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

# export/营期名称/导师名称/课程名称
@app.route("/export/<camp_name>/<coach_name>/<course_name>", methods=["GET"])
@app.route("/export/<camp_name>/<coach_name>/", defaults={"course_name": None}, methods=["GET"])
def export_works_csv(camp_name, coach_name, course_name):
    filename = "students.csv"
    try:
        lx_api = LanXin_API(username, password, base_url)
        lx_service = LanXin_service(api=lx_api)
        lx_service.flow_export_student_work(camp_name=camp_name, coach_name=coach_name, course_name=course_name)
        dir = BASE_PATH
        return send_from_directory(dir, filename, as_attachment=True)
    except Exception as e:
        return f"【有错误！快截图发 hy 看看】: {e}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)