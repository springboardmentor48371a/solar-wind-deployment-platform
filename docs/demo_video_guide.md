# Milestone 1 - Demo Video Guide & Presentation Script
**Objective**: A structured guide to help you record a clear, 3-to-5 minute video demonstrating your completed work for Milestone 1.

---

## 📽️ Video Structure & Script Agenda

### Part 1: Intro & Objective (approx. 30 seconds)
* **What to show**: The main landing page in your browser.
* **What to say**:
  > *"Hello Mam, in this video, I will demonstrate the completed Milestone 1 deliverables for the **Solar & Wind Deployment Intelligence Platform**.*
  > 
  > *This milestone sets up our full-stack project skeleton, initializing a React + TypeScript frontend, a FastAPI backend server, and a relational SQL database layer. Our core focus was creating a secure user registration and login gateway wrapped in an animated, clean-tech themed visual interface."*

---

### Part 2: Visual Interface & Responsive Design (approx. 1 minute)
* **What to show**: The login card and background graphics.
* **What to do**: Hover over the elements and slowly shrink the browser window to simulate a mobile viewport.
* **What to say**:
  > *"As you can see on the landing page, we replaced the generic gradient styling with a custom-engineered **Clean-Tech SVG environment**. This visually communicates the platform's purpose:*
  > * *The three wind turbines rotate at independent rotor speeds.*
  > * *The solar panels feature a sweeping light reflection glint.*
  > * *Floating breeze lines and drifting clouds simulate wind flow.*
  > * *Pulsing green network nodes represent a smart energy grid.*
  > 
  > *The animation uses clean, lightweight CSS keyframes, respecting the OS 'prefers-reduced-motion' settings. Additionally, the interface is fully responsive: if I shrink the screen to a mobile size, the heavy graphics hide automatically, and the card centers for a readable, clean layout."*

---

### Part 3: Secure User Authentication Flow (approx. 1.5 minutes)
* **What to do**: 
  1. Click **Create Account**. Try entering a short password (e.g., `123`) or mismatched passwords to trigger validation alerts.
  2. Register a new test user successfully (e.g., Name: `Hasini`, Email: `hasinimaddula26@gmail.com`).
  3. Show the redirection to the **Platform Dashboard**.
  4. Point out the dashboard details.
  5. Click **Sign Out** to show immediate session cleanup and route lock.
* **What to say**:
  > *"Now, let's demonstrate the user authentication flow. If I navigate to the registration tab and try to register with a short password, the interface prompts a validation warning.*
  > 
  > *Let's create a new account. When I click 'Register New Account', the frontend validates inputs and sends a secure POST request to the backend. The backend hashes the password using the bcrypt algorithm and creates the database record.*
  > 
  > *Upon successful registration, the user is logged in automatically and redirected to the protected dashboard view. We retrieve a signed JSON Web Token (JWT) which is stored in localStorage. The dashboard safely displays the user's name, email, and authentication status. Notice that the raw JWT token is hidden from the UI to protect credentials.*
  > 
  > *If I click 'Sign Out', the token is cleared from the browser, and the route guards instantly lock the dashboard, redirecting us back to the sign-in screen."*

---

### Part 4: Backend API & Database Inspection (approx. 1 minute)
* **What to show**:
  1. Switch tab to the FastAPI Swagger UI (`http://127.0.0.1:8000/docs`).
  2. Switch to your terminal window in the `backend/` directory and run: `python view_db.py`.
* **What to say**:
  > *"On the backend side, FastAPI automatically generates our interactive API documentation under Swagger UI, detailing our auth routes and validation schemas. We can test endpoints directly from here.*
  > 
  > *To verify that our user records are written to a real relational database, I'll run this database visualizer tool in my terminal. Running 'python view_db.py' connects to the active database, displays the schema columns of our 'users' table, and prints the registered user records—including the new account we just registered, with its password securely stored as a salted bcrypt hash.*
  > 
  > *This concludes the demo for Milestone 1. The full-stack authentication flow is fully functional and ready for deployment."*
