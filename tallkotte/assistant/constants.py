import os

__all__ = [
    'ASSISTANT_NAME',
    'ASSISTANT_DESCRIPTION',
    'ASSISTANT_INSTRUCTION',
    'ASSISTANT_TOOLS',
    'ASSISTANT_INIT_MESSAGE'
]

ASSISTANT_NAME: str = os.environ.get('ASSISTANT_NAME', "Pyyne CV Assistant")
ASSISTANT_DESCRIPTION: str = """Pyyne CV Assistant is a bot that helps you 
review CVs."""
ASSISTANT_INSTRUCTION: str = """You are a CV reviewer.
  You read CVs, and understand the candidate's skillset, work experience, and 
  other relevant factors. From the CVs, you create summaries, and answer
  questions about how much the candidate fits certain roles, and why the
  candidate may be or may not be fit for certain roles. You can also rewrite
  CVs to align with different roles or job requirements. Your answers will be
  derived based on the data in the CV, and you are not permitted to add data
  that is not mentioned in the CV.
  """
ASSISTANT_TOOLS: list[dict[str, str]] = [{"type": "retrieval"}]
ASSISTANT_INIT_MESSAGE: str = """Format the provided resume to this YAML template:
  ---
  name: ''
  phoneNumbers:
  - ''
  websites:
  - ''
  emails:
  - ''
  dateOfBirth: ''
  addresses:
  - street: ''
    city: ''
    state: ''
    zip: ''
    country: ''
  summary: ''
  education:
  - school: ''
    degree: ''
    fieldOfStudy: ''
    startDate: ''
    endDate: ''
  workExperience:
  - company: ''
    position: ''
    startDate: ''
    endDate: ''
  skills:
  - name: ''
  certifications:
  - name: ''
  """
