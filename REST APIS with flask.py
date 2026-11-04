# app/tasks/routes.py - Task API Endpoints
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Task, User
from app.utils.validators import validate_task_data
from app.utils.decorators import paginate
from app.utils.responses import success_response, error_response

class TaskListResource(Resource):
    """Resource for listing and creating tasks"""
    
    @jwt_required()
    def get(self):
        """Get list of tasks with pagination and filtering"""
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        priority = request.args.get('priority')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = Task.query.filter_by(user_id=current_user_id)
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        if priority:
            query = query.filter_by(priority=priority)
        
        # Apply sorting
        if hasattr(Task, sort_by):
            column = getattr(Task, sort_by)
            if sort_order == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        
        # Paginate results
        paginated_tasks = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Prepare response
        tasks_data = [{
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        } for task in paginated_tasks.items]
        
        return success_response({
            'tasks': tasks_data,
            'pagination': {
                'page': paginated_tasks.page,
                'per_page': paginated_tasks.per_page,
                'total_pages': paginated_tasks.pages,
                'total_items': paginated_tasks.total,
                'has_next': paginated_tasks.has_next,
                'has_prev': paginated_tasks.has_prev
            }
        })
    
    @jwt_required()
    def post(self):
        """Create a new task"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate input data
        validation_result = validate_task_data(data)
        if not validation_result['valid']:
            return error_response(validation_result['errors'], 400)
        
        # Create new task
        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date'),
            user_id=current_user_id
        )
        
        db.session.add(task)
        db.session.commit()
        
        return success_response({
            'message': 'Task created successfully',
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'created_at': task.created_at.isoformat()
            }
        }, 201)

class TaskResource(Resource):
    """Resource for single task operations"""
    
    @jwt_required()
    def get(self, task_id):
        """Get a specific task"""
        current_user_id = get_jwt_identity()
        
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        
        if not task:
            return error_response('Task not found', 404)
        
        return success_response({
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
        })
    
    @jwt_required()
    def put(self, task_id):
        """Update a task"""
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        
        if not task:
            return error_response('Task not found', 404)
        
        # Validate update data
        validation_result = validate_task_data(data, update=True)
        if not validation_result['valid']:
            return error_response(validation_result['errors'], 400)
        
        # Update task fields
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'priority' in data:
            task.priority = data['priority']
        if 'due_date' in data:
            task.due_date = data['due_date']
        
        db.session.commit()
        
        return success_response({
            'message': 'Task updated successfully',
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'updated_at': task.updated_at.isoformat()
            }
        })
    
    @jwt_required()
    def delete(self, task_id):
        """Delete a task"""
        current_user_id = get_jwt_identity()
        
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        
        if not task:
            return error_response('Task not found', 404)
        
        db.session.delete(task)
        db.session.commit()
        
        return success_response({'message': 'Task deleted successfully'}, 204)