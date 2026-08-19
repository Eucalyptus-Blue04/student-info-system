from db import db, User, Student, Department, Major, Grade, Class, StudentStatus
from app import app
from datetime import datetime

# 生成测试数据（不再创建或删除表结构）
with app.app_context():
    # 院系
    dep1 = Department(name='信息工程学院', description=None)
    dep2 = Department(name='医学院', description=None)
    dep3 = Department(name='机电工程学院', description=None)
    dep4 = Department(name='美术与艺术学院', description=None)
    dep5 = Department(name='外国语学院', description=None)
    db.session.add_all([dep1, dep2, dep3, dep4, dep5])
    db.session.commit()

    # 专业
    major1 = Major(name='计算机应用工程', department_id=dep1.id, description=None)
    major2 = Major(name='软件工程', department_id=dep1.id, description=None)
    major3 = Major(name='英语', department_id=dep5.id, description=None)
    major4 = Major(name='兽医', department_id=dep2.id, description=None)
    major5 = Major(name='自动化', department_id=dep3.id, description=None)
    major6 = Major(name='环境艺术设计', department_id=dep4.id, description=None)

    db.session.add_all([major1, major2, major3, major4, major5, major6])
    db.session.commit()

    # 年级
    grade1 = Grade(year=2022, name='2022级')
    grade2 = Grade(year=2023, name='2023级')
    grade3 = Grade(year=2024, name='2024级')
    grade4 = Grade(year=2025, name='2025级')
    db.session.add_all([grade1, grade2, grade3, grade4])
    db.session.commit()

    # 教师
    teacher1 = User(username='teacher01', password='123456', real_name='张三老师', role='teacher', phone='13800000001', email='teacher01@test.com')
    teacher2 = User(username='teacher02', password='123456', real_name='李四老师', role='teacher', phone='13800000002', email='teacher02@test.com')
    teacher3 = User(username='teacher03', password='123456', real_name='王五老师', role='teacher', phone='13800000003', email='teacher03@test.com')
    teacher4 = User(username='teacher04', password='123456', real_name='赵六老师', role='teacher', phone='13800000004', email='teacher04@test.com')
    teacher5 = User(username='teacher05', password='123456', real_name='钱七老师', role='teacher', phone='13800000005', email='teacher05@test.com')
    db.session.add_all([teacher1, teacher2, teacher3, teacher4, teacher5])
    db.session.commit()

    # 班级
    class1 = Class(name='2022计算机应用工程01班', grade_id=grade1.id, major_id=major1.id, teacher_id=teacher1.id)
    class2 = Class(name='2022软件工程01班', grade_id=grade1.id, major_id=major2.id, teacher_id=teacher2.id)
    class3 = Class(name='2024兽医01班', grade_id=grade3.id, major_id=major4.id, teacher_id=teacher4.id)
    class4 = Class(name='2024自动化01班', grade_id=grade3.id, major_id=major5.id, teacher_id=teacher5.id)
    class5 = Class(name='2022计算机应用工程02班', grade_id=grade1.id, major_id=major1.id, teacher_id=teacher1.id)
    class6 = Class(name='2022计算机应用工程03班', grade_id=grade1.id, major_id=major1.id, teacher_id=teacher1.id)
    class7 = Class(name='2024环境艺术设计01班', grade_id=grade2.id, major_id=major6.id, teacher_id=teacher3.id)
    class8 = Class(name='2023英语01班', grade_id=grade2.id, major_id=major3.id, teacher_id=teacher3.id)
    db.session.add_all([class1, class2, class3, class4, class5, class6, class7, class8])
    db.session.commit()
    #学生
    stu1 = Student(user_id=None, student_id='22013210105', name='赵甲', gender='男', age=21, class_id=class1.id, status=StudentStatus.ACTIVE.value, admission_date=datetime(2022, 9, 10), phone='13800001001', email='student01@test.com', address='示例地址1')
    db.session.add(stu1)
    db.session.commit()
    user1 = User(username=stu1.student_id, password='123456', real_name=stu1.name, role='student', email=stu1.email, phone=stu1.phone)
    db.session.add(user1)
    db.session.commit()
    stu1.user_id = user1.id
    db.session.add(stu1)
    db.session.commit()
    stu2 = Student(user_id=None, student_id='22013210106', name='钱乙', gender='女', age=20, class_id=class1.id, status=StudentStatus.ACTIVE.value, admission_date=datetime(2022, 9, 10), phone='13800001002', email='student02@test.com', address='示例地址2')
    db.session.add(stu2)
    db.session.commit()
    user2 = User(username=stu2.student_id, password='123456', real_name=stu2.name, role='student', email=stu2.email, phone=stu2.phone)
    db.session.add(user2)
    db.session.commit()
    stu2.user_id = user2.id
    db.session.add(stu2)
    db.session.commit()
    stu3 = Student(user_id=None, student_id='23013210107', name='孙丙', gender='男', age=19, class_id=class4.id, status=StudentStatus.ACTIVE.value, admission_date=datetime(2023, 9, 10), phone='13800001003', email='student03@test.com', address='示例地址3')
    db.session.add(stu3)
    db.session.commit()
    user3 = User(username=stu3.student_id, password='123456', real_name=stu3.name, role='student', email=stu3.email, phone=stu3.phone)
    db.session.add(user3)
    db.session.commit()
    stu3.user_id = user3.id
    db.session.add(stu3)
    db.session.commit()
    stu4 = Student(user_id=None, student_id='24013210108', name='李丁', gender='女', age=18, class_id=class8.id, status=StudentStatus.ACTIVE.value, admission_date=datetime(2024, 9, 10), phone='13800001004', email='student04@test.com', address='示例地址4')
    db.session.add(stu4)
    db.session.commit()
    user4 = User(username=stu4.student_id, password='123456', real_name=stu4.name, role='student', email=stu4.email, phone=stu4.phone)
    db.session.add(user4)
    db.session.commit()
    stu4.user_id = user4.id
    db.session.add(stu4)
    db.session.commit()

    
    print('测试数据已生成！')