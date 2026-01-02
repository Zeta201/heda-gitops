from pydantic import BaseModel

class InitRequest(BaseModel):
    experiment_name: str

class InitResponse(BaseModel):
    repo_url: str
    message: str

class PublishResponse(BaseModel):
    experiment_id: str
    pr_url: str
    message: str

class OnboardRequest(BaseModel):
    github_username: str
    
class OnboardStatusResponse(BaseModel):
    onboarded: bool
    invitation: str
    
class CreateExperimentResponse(BaseModel):
    experiment_id: str
    repo_url: str

class CreateExperimentRequest(BaseModel):
    exp_name: str
