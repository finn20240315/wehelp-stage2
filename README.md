# Taipei Day Trip Website

This is a travel-themed website focused on Taipei, offering a complete flow from browsing attractions, reserving tours, member login, online payments, to order confirmation. The project is fully deployed on AWS EC2.
---

## Key Features

#### Attraction Browsing & Search
- Supports keyword search and category filtering
- Dynamic data loading using AJAX / Fetch API
- Infinite scroll for paginated attraction listings

![Attraction Browsing & Search](week9/static/images/readme-Attraction%20Browsing%20%26%20Search.png)

#### Tour Reservation
- Users can log in to reserve attractions, select date and time slots
- Personal reservation management available after login
  
![Tour Reservation](week9/static/images/readme-Tour%20Reservation.png)

#### User Registration & Login System
- Implements secure login with JWT Token authentication
- UI dynamically switches based on login status
  
![User Registration & Login System](week9/static/images/readme-User%20Registration%20%26%20Login%20System.png)

#### TapPay Payment Integration
- Integrated with TapPay Prime API
- Users can pay securely using credit cards
- Redirects to the success page (/thankyou) upon payment confirmation
  
![TapPay Payment Integration](week9/static/images/readme-TapPay%20Payment%20Integration.png)

#### Order & Payment Workflow
- Successfully creates and stores orders in the database
- Calls TapPay API to validate transaction status
- Provides order number for user reference and confirmation
  
![Order & Payment Workflow](week9/static/images/readme-Order%20%26%20Payment%20Workflow.png)

---

## Technology Stack & Architecture

Category	Technology
---
Frontend	HTML, CSS, JavaScript, Fetch API
Backend	Python, FastAPI
Database	MySQL (Hosted on AWS RDS)
Third-Party	TapPay Payment API
Deployment	AWS EC2 + Uvicorn + Nginx + HTTPS
Auth System	JWT Token

---

## Project Structure Overview
![Project Structure Overview](week9/static/images/readme-Project%20Structure%20Overview.png)

