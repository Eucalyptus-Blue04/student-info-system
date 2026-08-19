import pytest
from db import User, UserRole, Department, Student
from datetime import datetime


class TestLoginRoute:
    """登录路由测试"""

    def test_login_page_loads(self, client):
        """测试登录页面加载"""
        response = client.get('/login')
        assert response.status_code == 200
        assert '用户登录' in response.data.decode('utf-8')

    def test_login_redirect_to_index(self, client):
        """测试首页重定向到登录"""
        response = client.get('/', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_captcha_endpoint(self, client):
        """测试验证码接口"""
        response = client.get('/captcha')
        assert response.status_code == 200
        assert response.content_type == 'image/png'


class TestStudentRoutes:
    """学生路由测试"""

    def test_students_requires_login(self, client):
        """测试学生列表需要登录"""
        response = client.get('/students', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location

    def test_students_page_with_auth(self, auth_client):
        """测试登录后访问学生列表"""
        response = auth_client.get('/students')
        assert response.status_code == 200

    def test_create_student_requires_admin(self, client, db):
        """测试创建学生需要管理员权限"""
        # 创建普通学生用户
        user = User(
            username='student1',
            password='123',
            role=UserRole.STUDENT.value
        )
        db.session.add(user)
        db.session.commit()

        # 学生登录
        client.post('/login', data={
            'username': 'student1',
            'password': '123',
            'captcha': 'test'
        })

        # 尝试创建学生
        response = client.get('/student/create', follow_redirects=False)
        # 应该被重定向或返回403
        assert response.status_code in [302, 403]


class TestDepartmentRoutes:
    """院系路由测试"""

    def test_departments_requires_admin(self, auth_client, db):
        """测试院系管理需要管理员权限"""
        response = auth_client.get('/departments')
        assert response.status_code == 200

    def test_create_department(self, auth_client, db):
        """测试创建院系"""
        response = auth_client.post('/department/create', data={
            'name': '新学院',
            'description': '测试学院'
        }, follow_redirects=True)

        assert response.status_code == 200

        # 验证院系已创建
        dept = Department.query.filter_by(name='新学院').first()
        assert dept is not None

    def test_create_duplicate_department(self, auth_client, db):
        """测试创建重复院系"""
        # 先创建一个院系
        dept = Department(name='已存在学院')
        db.session.add(dept)
        db.session.commit()

        # 尝试创建同名院系
        response = auth_client.post('/department/create', data={
            'name': '已存在学院',
            'description': '重复'
        }, follow_redirects=True)

        assert '院系已存在' in response.data.decode('utf-8')


class TestAPIRoutes:
    """API路由测试"""

    def test_get_majors_api(self, auth_client, db):
        """测试获取专业列表API"""
        # 创建测试数据
        dept = Department(name='测试学院')
        db.session.add(dept)
        db.session.flush()

        from db import Major
        major = Major(name='测试专业', department_id=dept.id)
        db.session.add(major)
        db.session.commit()

        # 调用API
        response = auth_client.get(f'/api/majors?department_id={dept.id}')
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) == 1
        assert data[0]['name'] == '测试专业'

    def test_get_majors_missing_param(self, auth_client):
        """测试缺少参数的专业API"""
        response = auth_client.get('/api/majors')
        assert response.status_code == 400

    def test_get_classes_api(self, auth_client, db):
        """测试获取班级列表API"""
        from db import Major, Grade, Class

        dept = Department(name='测试学院')
        db.session.add(dept)
        db.session.flush()

        major = Major(name='测试专业', department_id=dept.id)
        db.session.add(major)
        db.session.flush()

        grade = Grade(year=2024, name='2024级')
        db.session.add(grade)
        db.session.flush()

        class_ = Class(name='测试班', grade_id=grade.id, major_id=major.id)
        db.session.add(class_)
        db.session.commit()

        response = auth_client.get(f'/api/classes?major_id={major.id}')
        assert response.status_code == 200

        data = response.get_json()
        assert len(data) == 1


class TestTaskRoutes:
    """异步任务路由测试"""

    def test_task_status_endpoint(self, auth_client):
        """测试任务状态查询接口"""
        response = auth_client.get('/task/test-task-id/status')
        assert response.status_code == 200

        data = response.get_json()
        assert 'task_id' in data
        assert 'status' in data