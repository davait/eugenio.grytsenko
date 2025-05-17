🎯 Scenario:
You're building a lightweight API that takes in PDF or image resumes, runs OCR + LLM, and returns a structured JSON schema with name, contact info, experience, and skills.
 
The goal is to design and implement a small, functional prototype that reflects the core data flow.
 
💻 What You'll Do:
Set up a REST API (can be FastAPI/Flask or Cloud Function-style).
 
Accept file uploads (PDF, PNG, or JPG).
 
Call a mock OCR function (or real OCR lib like Tesseract or GCP Vision).
 
Simulate a call to Gemini/GPT with an LLM prompt to extract structured data.
 
Return structured JSON (e.g., {"name": ..., "email": ..., "skills": [...], "experience": [...]}).
 
 
Take 5min to think the solution. Decide what architecture attributes are desirable for this kind of project and implement accordingly as much as possible.
You can use LLMs to vibe code and also ask about concepts or design strategies.
Always express verbally your steps and your thoughts on the LLM responses.
