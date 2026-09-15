
-------------------------HOSPITAL MANAGEMENT SYSTEM----------------------------------

------Create Table for Patients------

CREATE TABLE Patients(Patient_ID INT PRIMARY KEY,Patient_Name VARCHAR(50),Gender VARCHAR(10),
Age INT, City VARCHAR(50),Mobile_No VARCHAR(15), Email VARCHAR(100),Registration_Date DATE);

insert into Patients values(101,'Arun','Male',25,'Chennai','9876543210','arun@gmail.com','2025-01-10'),
(102,'Sathya','Female',22,'Madurai','9876543211','sathya@gmail.com','2025-02-15'),
(103,'Priya','Female',30,'Trichy','9876543212','priya@gmail.com','2024-12-20'),
(104,'Suresh','Male',35,'Chennai','9876543213','suresh@gmail.com','2025-03-05'),
(105,'Divya','Female',28,'Coimbatore','9876543214','divya@gmail.com','2025-04-12'),
(106,'Saranya','Female',26,'Madurai','9876543215','saranya@gmail.com','2025-05-20');


------create Table for Doctors-----

CREATE TABLE Doctors( Doctor_ID INT PRIMARY KEY, Doctor_Name VARCHAR(50), Specialization VARCHAR(50),
Consultation_Fee DECIMAL(10,2));

insert into Doctors values(201,'Dr. Kumar','Cardiologist',500),
(202,'Dr. Meena','Dermatologist',800),
(203,'Dr. Ravi','Neurologist',900),
(204,'Dr. John','Orthopedic',1000),
(205,'Dr. Priya','Pediatrician',600);









------create Table for Appointments------

CREATE TABLE Appointments(Appointment_ID INT PRIMARY KEY,Patient_ID INT,Doctor_ID INT,Appointment_Date DATE,
FOREIGN KEY (Patient_ID) REFERENCES Patients(Patient_ID),FOREIGN KEY (Doctor_ID) REFERENCES Doctors(Doctor_ID));

insert into Appointments values(301,101,201,'2025-01-15'),
(302,102,202,'2025-02-18'),
(303,103,203,'2025-01-05'),
(304,104,204,'2025-03-08'),
(305,105,205,'2025-04-15'),
(306,106,202,'2025-05-22'),
(307,101,203,'2025-06-10'),
(308,102,201,'2025-06-18');


------create Table for Bills------

CREATE TABLE Bills(Bill_ID INT PRIMARY KEY,Patient_ID INT,Bill_Amount DECIMAL(10,2),Payment_Amount DECIMAL(10,2), Payment_Date DATE,
FOREIGN KEY (Patient_ID) REFERENCES Patients(Patient_ID));

insert into Bills values(401,101,2500,2500,'2025-01-15'),
(402,102,1800,1000,'2025-02-18'),
(403,103,3200,0,'2025-01-05'),
(404,104,1500,1500,'2025-03-08'),
(405,105,1200,1200,'2025-04-15'),
(406,106,2000,500,'2025-05-22');




------Question 1------

SELECT*FROM Patients WHERE Registration_Date > '2025-01-01';


------Question 2------


SELECT DISTINCT Specialization FROM Doctors;











------Question 3------

SELECT*FROM Patients WHERE Patient_Name LIKE 'S%'
AND City IN ('Chennai','Madurai');











------Question 4------

SELECT*FROM Doctors WHERE Consultation_Fee BETWEEN 500 AND 1500;











------Question 5------

 SELECT*FROM Doctors ORDER BY Consultation_Fee DESC LIMIT 5;
















------Question 6------

SELECT Doctor_ID,COUNT(*) AS Total_Appointments FROM Appointments GROUP BY Doctor_ID;
















------Question 7------

SELECT Doctor_ID,COUNT(*) AS Total_Appointments FROM Appointments GROUP BY Doctor_ID HAVING COUNT(*)>1;










------Question 8-------

SELECT SUM(Bill_Amount) AS Total_Bill,AVG(Bill_Amount) AS Average_Bill,
MAX(Bill_Amount) AS Maximum_Bill,MIN(Bill_Amount) AS Minimum_Bill FROM Bills;

















-------Question 9------

SELECT P.Patient_Name, D.Doctor_Name, A.Appointment_Date FROM Patients P INNER JOIN Appointments A ON P.Patient_ID=A.Patient_ID
INNER JOIN Doctors D ON D.Doctor_ID=A.Doctor_ID;












------Question 10------

SELECT P.Patient_Name,D.Doctor_Name,B.Bill_Amount,B.Payment_Date FROM Patients P JOIN
Appointments A ON P.Patient_ID=A.Patient_ID JOIN Doctors D ON A.Doctor_ID=D.Doctor_ID
JOIN Bills B ON P.Patient_ID=B.Patient_ID;





-----Question 11-------

SELECT*FROM Patients WHERE Patient_ID NOT IN(SELECT Patient_ID FROM Bills WHERE Payment_Amount>0);










-----Question 12-------

SELECT*FROM Patients WHERE Patient_ID IN(SELECT Patient_ID FROM Bills
WHERE Bill_Amount >(SELECT AVG(Bill_Amount)FROM Bills));









-----Question 13-------

SELECT Doctor_ID,COUNT(*) AS Total_Appointments FROM Appointments GROUP BY Doctor_ID
ORDER BY Total_Appointments DESC LIMIT 3;









-----Question 14-------

SELECT Mobile_No,COUNT(*)FROM Patients GROUP BY Mobile_No HAVING COUNT(*)>1;






-----Question 15-------

SELECT*FROM Patients WHERE Mobile_No IS NULL OR Email IS NULL;








-----Question 16-------

String Functions SELECT UPPER(Patient_Name) AS Upper_Name,LEFT(Patient_Name,5) AS First_Five,
LENGTH(Patient_Name) AS Name_Length FROM Patients;


-----Question 17-------

CASE WHEN (Doctor Category) 
SELECT Doctor_Name,Consultation_Fee,
CASE
WHEN Consultation_Fee<700 THEN 'Junior'
WHEN Consultation_Fee BETWEEN 700 AND 1200 THEN 'Senior'
ELSE 'Specialist'
END AS Doctor_Category
FROM Doctors;


-----Question 18------

CASE WHEN (Bill Status)
SELECT
Bill_ID,
Bill_Amount,
Payment_Amount,
CASE
WHEN Payment_Amount=Bill_Amount THEN 'Paid'
WHEN Payment_Amount>0 THEN 'Partially Paid'
ELSE 'Pending'
END AS Payment_Status
FROM Bills;


------Question 19------

CREATE INDEX idx_patient ON Appointments(Patient_ID);

CREATE INDEX idx_doctor ON Appointments(Doctor_ID);


-----Question 20------

Patient Name, Doctor Name, Total Bill Amount, Payment Status SELECT P.Patient_Name,D.Doctor_Name,SUM(B.Bill_Amount) AS Total_Bill_Amount,
CASE
WHEN SUM(B.Payment_Amount)=SUM(B.Bill_Amount) THEN 'Paid'
WHEN SUM(B.Payment_Amount)>0 THEN 'Partially Paid'
ELSE 'Pending'
END AS Payment_Status
FROM Patients P
JOIN Appointments A
ON P.Patient_ID=A.Patient_ID
JOIN Doctors D
ON A.Doctor_ID=D.Doctor_ID
JOIN Bills B
ON P.Patient_ID=B.Patient_ID
GROUP BY
P.Patient_Name,
D.Doctor_Name
ORDER BY Total_Bill_Amount DESC;




drop table 