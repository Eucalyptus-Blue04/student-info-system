import pytest
from db import User, Student, Department, Major, Grade, Class, StudentStatus, UserRole
from datetime import datetime


class TestUserModel:
    """用户模型测试"""

    def test_create_user(self, db):
        """测试创建用户"""
        user = User(
            username='testuser',
            password='test123',
            real_name='测试用户',
            role=UserRole.STUDENT.value
        )
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'testuser'
        assert user.role == 'student'

    def test_user_role_methods(self, db):
        """测试用户角色判断方法"""
        admin = User(username='admin', password='123', role=UserRole.ADMIN.value)
        teacher = User(username='teacher', password='123', role=UserRole.TEACHER.value)
        student = User(username='student', password='123', role=UserRole.STUDENT.value)

        assert admin.is_admin() is True
        assert admin.is_teacher() is False
        assert teacher.is_teacher() is True
        assert teacher.is_admin() is False

    def test_user_default_role(self, db):
        """测试默认角色"""
        user = User(username='default', password='123')
        assert user.role == UserRole.STUDENT.value


class TestStudentModel:
    """学生模型测试"""

    def test_create_student(self, db):
        """测试创建学生"""
        # 先创建关联数据
        dept = Department(name='测试学院')
        db.session.add(dept)
        db.session.flush()

        major = Major(name='测试专业', department_id=dept.id)
        db.session.add(major)
        db.session.flush()

        grade = Grade(year=2024, name='2024级')
        db.session.add(grade)
        db.session.flush()

        class_ = Class(name='2024测试专业01班', grade_id=grade.id, major_id=major.id)
        db.session.add(class_)
        db.session.flush()

        student = Student(
            student_id='2024001',
            name='张三',
            gender='男',
            age=18,
            class_id=class_.id,
            status=StudentStatus.ACTIVE.value,
            admission_date=datetime(2024, 9, 1)
        )
        db.session.add(student)
        db.session.commit()

        assert student.id is not None
        assert student.student_id == '2024001'
        assert student.status == '在读'

    def test_student_class_relationship(self, db):
        """测试学生与班级的关系"""
        dept = Department(name='测试学院')
        db.session.add(dept)
        db.session.flush()

        major = Major(name='测试专业', department_id=dept.id)
        db.session.add(major)

        grade = Grade(year=2024, name='2024级')
        db.session.add(grade)
        db.session.flush()

        class_ = Class(name='测试班', grade_id=grade.id, major_id=major.id)
        db.session.add(class_)
        db.session.flush()

        student = Student(
            student_id='2024001',
            name='张三',
            gender='男',
            age=18,
            class_id=class_.id,
            admission_date=datetime(2024, 9, 1)
        )
        db.session.add(student)
        db.session.commit()

        assert student.class_.name == '测试班'
        assert student.class_.major.name == '测试专业'


class TestDepartmentModel:
    """院系模型测试"""

    def test_create_department(self, db):
        """测试创建院系"""
        dept = Department(name='信息工程学院', description='工科学院')
        db.session.add(dept)
        db.session.commit()

        assert dept.id is not None
        assert dept.name == '信息工程学院'

    def test_department_major_relationship(self, db):
        """测试院系与专业的关系"""
        dept = Department(name='测试学院')
        db.session.add(dept)
        db.session.flush()

        major1 = Major(name='专业1', department_id=dept.id)
        major2 = Major(name='专业2', department_id=dept.id)
        db.session.add_all([major1, major2])
        db.session.commit()

        assert len(dept.majors) == 2