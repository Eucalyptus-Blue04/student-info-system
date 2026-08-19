from celery_worker import make_celery
from flask import Flask
from db import db, Student, User, StudentStatusChange, MajorTransfer
from datetime import datetime
import time

# 创建Flask应用并配置Celery
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

db.init_app(app)
celery = make_celery(app)


@celery.task(bind=True, name='tasks.send_status_change_notification')
def send_status_change_notification(self, student_id, old_status, new_status, reason):
    """异步发送学籍状态变更通知"""
    try:
        with app.app_context():
            student = Student.query.get(student_id)
            if not student:
                return {'status': 'error', 'message': '学生不存在'}

            # 模拟发送通知（实际项目中可对接邮件/短信服务）
            time.sleep(2)  # 模拟网络延迟

            notification = {
                'type': 'status_change',
                'student_id': student.student_id,
                'student_name': student.name,
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat(),
                'message': f'您的学籍状态已从{old_status}变更为{new_status}'
            }

            print(f"[通知] 学生{student.name}: {notification['message']}")

            return {
                'status': 'success',
                'notification': notification
            }
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)


@celery.task(bind=True, name='tasks.send_transfer_result_notification')
def send_transfer_result_notification(self, transfer_id, action):
    """异步发送转专业审批结果通知"""
    try:
        with app.app_context():
            transfer = MajorTransfer.query.get(transfer_id)
            if not transfer:
                return {'status': 'error', 'message': '申请记录不存在'}

            student = Student.query.get(transfer.student_id)
            time.sleep(2)  # 模拟网络延迟

            status_text = '已通过' if action == 'approve' else '已拒绝'
            notification = {
                'type': 'transfer_result',
                'student_id': student.student_id,
                'student_name': student.name,
                'old_major': transfer.old_class.major.name,
                'new_major': transfer.new_major.name,
                'status': status_text,
                'timestamp': datetime.utcnow().isoformat(),
                'message': f'您的转专业申请已{status_text}'
            }

            print(f"[通知] 学生{student.name}: {notification['message']}")

            return {
                'status': 'success',
                'notification': notification
            }
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)


@celery.task(bind=True, name='tasks.batch_import_students')
def batch_import_students(self, students_data):
    """异步批量导入学生数据"""
    try:
        with app.app_context():
            success_count = 0
            fail_count = 0
            errors = []

            for index, data in enumerate(students_data):
                try:
                    # 检查学号是否已存在
                    if Student.query.filter_by(student_id=data['student_id']).first():
                        errors.append(f"行{index+1}: 学号{data['student_id']}已存在")
                        fail_count += 1
                        continue

                    student = Student(
                        student_id=data['student_id'],
                        name=data['name'],
                        gender=data['gender'],
                        age=int(data['age']),
                        class_id=int(data['class_id']),
                        status='在读',
                        admission_date=datetime.strptime(data['admission_date'], '%Y-%m-%d'),
                        phone=data.get('phone', ''),
                        email=data.get('email', ''),
                        address=data.get('address', '')
                    )
                    db.session.add(student)
                    success_count += 1

                    # 每100条提交一次
                    if (index + 1) % 100 == 0:
                        db.session.commit()

                    # 模拟处理耗时
                    time.sleep(0.1)

                except Exception as e:
                    errors.append(f"行{index+1}: {str(e)}")
                    fail_count += 1

            db.session.commit()

            result = {
                'status': 'success',
                'success_count': success_count,
                'fail_count': fail_count,
                'errors': errors[:10]  # 只返回前10条错误
            }

            print(f"[批量导入] 完成: 成功{success_count}条, 失败{fail_count}条")
            return result

    except Exception as e:
        db.session.rollback()
        self.retry(exc=e, countdown=60, max_retries=3)


@celery.task(bind=True, name='tasks.send_grade_report')
def send_grade_report(self, student_id):
    """异步生成并发送学籍报告"""
    try:
        with app.app_context():
            student = Student.query.get(student_id)
            if not student:
                return {'status': 'error', 'message': '学生不存在'}

            # 模拟生成报告
            time.sleep(3)

            report = {
                'student_id': student.student_id,
                'name': student.name,
                'department': student.class_.major.department.name,
                'major': student.class_.major.name,
                'class': student.class_.name,
                'status': student.status,
                'admission_date': student.admission_date.strftime('%Y-%m-%d'),
                'generated_at': datetime.utcnow().isoformat()
            }

            print(f"[报告] 已生成学生{student.name}的学籍报告")

            return {
                'status': 'success',
                'report': report
            }
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)