# Demo Walkthrough

1. Start the stack:
   ```bash
   make dev
   ```
2. Apply migrations:
   ```bash
   make migrate
   ```
3. Seed demo data:
   ```bash
   make seed
   ```
4. Log in:
   ```bash
   curl -X POST "http://localhost:8000/auth/login" -d "email=demo@example.com" -d "password=demo"
   ```
5. Fetch dashboard:
   ```bash
   curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/portfolio/dashboard
   ```
6. Generate a pack:
   ```bash
   curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/companies/1/pack
   ```
