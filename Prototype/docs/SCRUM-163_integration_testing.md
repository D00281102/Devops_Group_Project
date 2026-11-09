

\# SCRUM-163 — FastAPI and ControlDB Integration Testing



\*\*Developer:\*\* Simon  

\*\*Date:\*\* 6 November 2026



\## What I Worked On



For this task, I tested how FastAPI and ControlDB work together, from creating a building to managing membership and updating control settings.



I created a separate integration test file called `test\_scrum163\_integration.py` to check the full process automatically.



\## What I Tested



1\. Both database connections point to the test database.

2\. An authenticated user can create a building.

3\. Another user can request to join the building.

4\. Users with pending requests cannot access control settings.

5\. Building admins can view pending membership requests.

6\. Building admins can approve membership requests.

7\. Approved members can view control settings.

8\. Normal members cannot update control settings.

9\. Building admins can update control settings.

10\. Updated settings are saved correctly in PostgreSQL.



\## Test Results



All 10 integration checks passed.



The tests returned the expected HTTP responses, including:



\- `201 Created` for building creation and membership requests.

\- `200 OK` for permitted actions.

\- `403 Forbidden` for unauthorized actions.



\*\*Result:\*\* SCRUM-163: ALL INTEGRATION TESTS PASSED



\*\*Test Building ID:\*\* 7



\## Test Environment



\- FastAPI TestClient

\- PostgreSQL ControlDB

\- Database: `controldb\_combined\_test`

\- PostgreSQL port: `5435`



I used the isolated test database so the main project database wasn't affected.



\## How to Run the Test



From the `Prototype` folder, run:



```cmd

python test\_scrum163\_integration.py

```



The test requires a running PostgreSQL test database, the existing test users, and the local authentication configuration. Database passwords and JWT secrets are not included in this document.



Each run creates a new test building and membership records in the isolated test database.



\## Git Information



\*\*Branch:\*\* `SCRUM-158-simon-building-access`



\*\*Integration Test Commit:\*\* `d7538df`



\## Conclusion



The integration tests passed, confirming that building creation, membership management, access permissions and control settings work together through FastAPI and ControlDB.



I also captured the successful test results as evidence for Jira.



