import requests
import json
import csv
import logging

"""

"""

logger = logging.getLogger(name="lx_api")
consle = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
consle.setFormatter(formatter)
logger.addHandler(consle)


class LanXin_API:
    def __init__(self, username: str, password: str, base_url: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.headers = {"Authorization": f"Bearer {self.get_token()}"}

    def get_token(self):
        url = ''.join([self.base_url, "jwt/"])
        data = {"username": self.username, "password": self.password}
        logger.info(f"[POST] ==>  URL={url}  PARAMS={data}")
        res = requests.post(url=url, json=data, verify=False)
        res = json.loads(res.text)
        return res.get("token")

    def get_classes_by_camp_id(self, camp_id: int, limit: int = 100):
        """
        获取营期信息
        """
        url = ''.join([self.base_url, f"crm/v1/classes/"])
        data = {
            "period_id": camp_id,
            "limit": limit
        }
        logger.info(f"[GET] ==>  URL={url}  HEADER={self.headers}  PARAMS={data}")
        res = requests.get(url=url, headers=self.headers, params=data)
        res = json.loads(res.text)
        return res.get("results")

    def get_camps(self, limit: int = 100):
        """
        获取营期信息
        """
        url = ''.join([self.base_url, f"crm/v1/camps/?limit={limit}"])
        logger.info(f"[GET] ==>  URL={url}  HEADER={self.headers}")
        res = requests.get(url=url, headers=self.headers)
        res = json.loads(res.text)
        camp_list = res.get("results")
        return camp_list

    def get_user_answers(self, camp_id: int, class_id: int, course_name: str = None, is_pick: bool = True,
                         comment_type: int = None, page: int = 1, limit: int = 100):
        """
        获取学员作业
        """
        url = ''.join([self.base_url, f"crm/v1/user_answers"])
        data = {
            "ordering": '-submit_time',
            "is_pick": is_pick,
            "period_id": camp_id,
            "class_id": class_id,
            "exercise_name": course_name,
            "comment_type": comment_type,
            "page": page,
            "limit": limit
        }
        logger.info(f"[GET] ==>  URL={url}  HEADER={self.headers}  PARAMS={data}")
        res = requests.get(url=url, headers=self.headers, params=data)
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

    def search_student_works_by_camp_and_coach(self, camp_name: str, coach_name: str, course_name: str = None,
                                               is_pick=True, comment_type=None):
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

        answer_res = self.api.get_user_answers(camp_id=camp_id, class_id=class_id, course_name=course_name, comment_type=comment_type, page=1,
                                               is_pick=is_pick)
        all_answers = answer_res.get("results")
        total_answer = answer_res.get("count")
        count_answer = total_answer - 50
        p = 1  # 页码
        while count_answer > 0:
            p += 1  # 翻页
            count_answer -= 50
            answers = self.api.get_user_answers(camp_id=camp_id, class_id=class_id, course_name=course_name, comment_type=comment_type, page=p,
                                                is_pick=is_pick)
            all_answers.extend(answers.get("results"))

        return all_answers

    def _export_student_to_csv(self, student_list):
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

    def flow_export_student_work(self, camp_name: str, coach_name: str, course_name: str = None, is_pick: bool = True, comment_type: int = None):
        print("正在获取学员信息..")
        works = self.search_student_works_by_camp_and_coach(camp_name, coach_name, course_name=course_name,
                                                            is_pick=is_pick, comment_type=comment_type)
        print(f"获取完成: 共 {len(works)} 条")
        print("正在导出学员信息..")
        count = self._export_student_to_csv(works)
        print(f"导出完成: 共 {count} 条")

    def flow_count_first_comment_work(self, camp_name: str, coach_name: str, course_name:str = None):
        """
        统计学生作业初评次数
        """
        students = self.search_student_works_by_camp_and_coach(
            camp_name=camp_name,
            coach_name=coach_name,
            course_name=course_name,
            is_pick=False,
            comment_type=1
            )
        results = {}
        for stu in students:
            nickname = stu.get("nickname")
            if nickname in results:
                results[nickname] += 1
            else:
                results[nickname] = 1
        
        results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1], reverse=True)}

        TITLE_ROW = ["学员别名", "初评次数"]
        c = 0
        with open("count_first_comment_work.csv", "w", encoding="utf_8_sig") as f:
            CSVWriter = csv.writer(f)
            CSVWriter.writerow(TITLE_ROW)
            for name, count in results.items():
                c += 1
                CSVWriter.writerow(
                    [
                        name,
                        count
                    ]
                )
        print("导出完成")
        return c



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
    # lx_service.flow_export_student_work(CAMP_NAME, COACH_NAME, is_pick=False, comment_type=1)
    print(lx_service.flow_count_first_comment_work(CAMP_NAME, COACH_NAME))
