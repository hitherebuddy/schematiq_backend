from .gemini_service import gemini_service
from prompts import PromptLibrary
import uuid

# Mock database
from config import Config
db = Config.DATABASE

class PlanService:
    def get_user_plans(self, user_id):
        return [plan for plan in db['plans'].values() if plan.get('user_id') == user_id]

    def create_new_plan(self, user_id, user_input, mode, extras=None):
        prompt = PromptLibrary.generate_base_plan(user_input, mode, extras)
        plan_data_json = gemini_service.generate_json_response(prompt)
        
        if isinstance(plan_data_json, dict) and 'error' in plan_data_json:
            return plan_data_json

        plan_id = plan_data_json.get('id', str(uuid.uuid4()))
        
        metadata_source = plan_data_json
        if 'steps' in plan_data_json and isinstance(plan_data_json['steps'], dict):
             metadata_source = plan_data_json['steps']
        
        steps_list = plan_data_json.get('steps')
        if isinstance(steps_list, dict):
            steps_list = steps_list.get('steps', [])

        new_plan = {
            "id": plan_id,
            "user_id": user_id,
            "title": metadata_source.get('title', user_input),
            "mode": mode,
            "estimated_duration": metadata_source.get('estimated_duration'),
            "budget_level": metadata_source.get('budget_level'),
            "tags": metadata_source.get('tags', []),
            "steps": steps_list if isinstance(steps_list, list) else [],
            "created_at": "timestamp_placeholder"
        }
        
        db['plans'][plan_id] = new_plan
        return new_plan
        
    def toggle_step_status(self, plan_id, step_id):
        plan = db['plans'].get(plan_id)
        if not plan:
            return {"error": "Plan not found"}, 404

        step_found = False
        for step in plan.get('steps', []):
            # Add a check to ensure we're dealing with a dictionary
            if isinstance(step, dict) and step.get('id') == step_id:
                step['is_complete'] = not step.get('is_complete', False)
                step_found = True
                break
        
        if not step_found:
            return {"error": "Step not found"}, 404
        
        return plan, 200

    def get_dynamic_replan(self, plan_id, step_id, outcome, reason=None):
        plan = db['plans'].get(plan_id)
        if not plan:
            return {"error": "Plan not found"}, 404

        import json
        plan_json_str = json.dumps(plan, indent=2)

        completed_step_title = ""
        for step in plan['steps']:
            if step['id'] == step_id:
                completed_step_title = step['title']
                break
        
        if not completed_step_title:
            return {"error": "Step to replan from not found"}, 404
        
        prompt = PromptLibrary.replan_based_on_outcome(plan_json_str, completed_step_title, outcome, reason)
        ai_response = gemini_service.generate_json_response(prompt)
        
        if isinstance(ai_response, dict) and 'error' in ai_response:
            return ai_response, 500

        # --- VALIDATION FIX FOR AI RESPONSE STRUCTURE ---
        validated_new_steps = []
        if isinstance(ai_response, list):
            # This is the expected, correct format
            validated_new_steps = ai_response
        elif isinstance(ai_response, dict) and 'steps' in ai_response and isinstance(ai_response['steps'], list):
            # This handles the case where the AI incorrectly returns a full plan object
            validated_new_steps = ai_response['steps']
        else:
            # The AI returned something completely unexpected
            print(f"Unexpected AI replan format: {ai_response}")
            return {"error": "AI returned an invalid format for the replan."}, 500
        # --- END OF FIX ---

        original_steps = plan['steps']
        new_plan_steps = []
        for step in original_steps:
            if isinstance(step, dict) and step.get('id') == step_id:
                step['is_complete'] = True
                new_plan_steps.append(step)
            elif isinstance(step, dict) and step.get('is_complete'):
                new_plan_steps.append(step)

        new_plan_steps.extend(validated_new_steps)
        plan['steps'] = new_plan_steps
        
        return plan, 200

    def get_ai_step_assistance(self, step_description, user_question):
        prompt = PromptLibrary.ask_ai_on_step(step_description, user_question)
        return gemini_service.generate_text_response(prompt)

    def get_step_decomposition(self, parent_step_title):
        prompt = PromptLibrary.decompose_step(parent_step_title)
        return gemini_service.generate_json_response(prompt)

# Singleton instance
plan_service = PlanService()