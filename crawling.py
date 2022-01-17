import requests
import json
import csv

"""
1.线上管理后台链接：http://pencil.ilanxin.cn/home
账号：cangjie
密码：sfilanxin
"""

class LanXin_API:
    def __init__(self, username: str, password: str, base_url: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.headers = {"Authorization": f"Bearer {self.get_token()}"}

    def get_token(self):
        url = "jwt/"
        data = {"username": self.username, "password": self.password}
        res = requests.post(url=''.join([self.base_url, url]), json=data, verify=False)
        res = json.loads(res.text)
        return res.get("token")

    def get_classes_by_camp_id(self, camp_id: int, limit: int=100):
        """
        获取营期信息
        """
        url = f"crm/v1/classes/"
        data = {
            "period_id": camp_id,
            "limit": limit
        }
        res = requests.get(url=''.join([self.base_url, url]), headers=self.headers, params=data)
        res = json.loads(res.text)
        return res.get("results")

    def get_camps(self, limit: int=100):
        """
        获取营期信息
        """
        url = f"crm/v1/camps/?limit={limit}"
        res = requests.get(url=''.join([self.base_url, url]), headers=self.headers)
        res = json.loads(res.text)
        camp_list = res.get("results")
        return camp_list

    def get_user_answers(self, camp_id:int, class_id: int, course_name: str=None, is_pick: bool=True, page: int=1, limit:int=100):
        """
        获取学员作业
        """
        url = f"crm/v1/user_answers"
        data = {
            "ordering": '-submit_time',
            "is_pick": is_pick,
            "period_id": camp_id,
            "class_id": class_id,
            "exercise_name": course_name,
            "page": page,
            "limit": limit
        }
        res = requests.get(url=''.join([self.base_url, url]), headers=self.headers, params=data)
        res = json.loads(res.text)
        return res
        

class LanXin_service:
    def __init__(self, api: LanXin_API):
        self.api = api

    def search_camps_by_name(self, search_name):
        camp_list = self.api.get_camps()
        camp_result_list = []
        for camp in camp_list:
            if search_name in camp.get("name"):
                camp_result_list.append(camp)
        return camp_result_list

    def search_student_works_by_camp_and_coach(self, camp_name: str, coach_name: str, course_name: str=None):
        """
        搜索学员作业
        """
        camp_list = self.search_camps_by_name(camp_name)
        assert len(camp_list) > 0, "错误: 营期班级名称不存在"
        assert len(camp_list) == 1, "错误: 营期班级名称不唯一"
        camp_id = camp_list[0].get("id")
        classes = self.api.get_classes_by_camp_id(camp_id=camp_id)
        class_id = None
        for class_ in classes:
            if coach_name == class_.get("name"):
                class_id = class_.get("id")
        if class_id is None:
            raise Exception(f"错误：导师名称【{coach_name}】不存在")
        all_answers = []

        answer_res = self.api.get_user_answers(camp_id=camp_id, class_id=class_id, course_name=course_name, page=1)
        all_answers = answer_res.get("results")
        total_answer = answer_res.get("count")
        count_answer = total_answer - 50
        p = 1  # 页码
        while count_answer > 0:
            p += 1  # 翻页
            count_answer -= 50
            answers = self.api.get_user_answers(camp_id=camp_id, class_id=class_id, course_name=course_name, page=p)
            all_answers.extend(answers.get("results"))

        return all_answers
    
    def export_student_to_csv(self, student_list):
        TITLE_ROW = ["学员ID", "微课ID", "学员别名", "老师别名", "作业名称", "作业"]
        count = 0
        with open("students.csv", "w", encoding="utf_8_sig") as f:
            CSVWriter = csv.writer(f)
            CSVWriter.writerow(TITLE_ROW)
            for student in student_list:
                count += 1
                CSVWriter.writerow(
                    [
                        student.get("user_id"),
                        student.get("weike_id"),
                        student.get("nickname"),
                        student.get("coach_alias"),
                        student.get("exercise_name"),
                        student.get("answer"),
                    ]
                )
        print("导出完成")
        return count

    def flow_export_student_work(self, camp_name: str, coach_name: str, course_name: str=None):
        print("正在获取学员信息..")
        works = self.search_student_works_by_camp_and_coach(camp_name, coach_name, course_name=course_name)
        print(f"获取完成: 共 {len(works)} 条")
        print("正在导出学员信息..")
        count = self.export_student_to_csv(works)
        print(f"导出完成: 共 {count} 条")


if __name__ == "__main__":

    CAMP_NAME = "17"
    COACH_NAME = "烟然老师"

    with open("credential.json") as f:
        credential = json.load(f)
    username = credential.get("username")
    password = credential.get("password")
    base_url = credential.get("base_url")

    lx_api = LanXin_API(username, password, base_url)
    lx_service = LanXin_service(api=lx_api)
    # student_list = lx_service.search_student_works_by_camp_and_coach(CAMP_NAME, COACH_NAME)
    # with open("students.json", "w", encoding="utf-8") as f:
    #     json.dump(student_list, f, ensure_ascii=False)
    lx_service.flow_export_student_work(CAMP_NAME, COACH_NAME)