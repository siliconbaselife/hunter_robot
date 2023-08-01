from dao.task_dao import query_job_requirement_db

def candidate_filter(job_id, candidate_info):
    job_requirement = query_job_requirement_db(job_id)
    
    return False