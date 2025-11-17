# 📅 BOACMS  
**Barangay Online Appointment and Certification Management System,** an online appointment and certification management system that streamlines the process of acquiring barangay certifications while enhancing accessibility, transparency, and efficiency in service delivery—ultimately improving citizen satisfaction and strengthening barangay governance.

### 🌐 TECH STACK USED  
**Backend**:  
> Django – Serves as the main backend framework, handling server-side logic, authentication, and database interactions.  
> Supabase – Provides the database and authentication services, offering a PostgreSQL backend with real-time capabilities and easy integration with Django.

**Frontend**:  
> HTML – Defines the structure and layout of the web pages.  
> CSS – Styles the user interface to ensure a clean and responsive design.  
> JavaScript – Adds interactivity and dynamic behavior to the frontend.

**Version Control:**  
> Git & GitHub – Used for source code management, version control, and team collaboration.

## 📄 Setup & run instructions
1. Clone the repository  
	`git clone https://github.com/adamxparx/CSIT327-G2-BOACMS.git`  

2. Change directory to the cloned project  
	`cd CSIT327-G2-BOACMS`  

4. Create the virtual environment  
	`python -m venv venv`  

5. Activate the virtual environment  
   	Windows: `venv\Scripts\activate`  
	MacOS/Linux: `source venv/bin/activate` 

7. Install the required packages  
	`pip install -r requirements.txt`  

9. Create .env file to store environment-specific variables.
    
	`# Supabase credentials`  
	`DB_ENGINE=django.db.backends.postgresql`  
	`DB_NAME=postgres`  
	`DB_USER=postgres.syqrwazhtflzztakolkj`  
	`DB_PASSWORD=[YOUR_PASSWORD]`  
	`DB_HOST=aws-1-ap-southeast-1.pooler.supabase.com`  
	`DB_PORT=5432` 
  
11. Run the server  
	`python manage.py runserver`

### 💻 LINK TO THE DEPLOYED APP (RENDER)
https://boacms-portal.onrender.com/

## 👥 THE TEAM

Inoc, Nicole John P.		(Product Owner)  		nicolejohn.inoc@cit.edu  
Lapis, Andrae Louise U.		(Business Analyst) 	andraelouise.lapis@cit.edu  
Lawas, Berchard Lawrence D.	(Business Analyst) 	berchardlawrence.lawas@cit.edu  
Leonardo, Natasha Kate A.	(Scrum Master) 		natashakate.leonardo@cit.edu  
  
Esparcia, Adam Cloyd H.		(Lead Developer) 		adamcloyd.esparcia@cit.edu  
Esparcia, Earl Gerald R.	(Developer) 		earlgerald.esparcia@cit.edu  
Estrada, Julianna Carmel 	(Developer)		juliannacarmel.estrada@cit.edu  
