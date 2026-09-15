# --- PATIENT REGISTRATION ---

def patient_registration():
    patient_id = int(input("Enter Patient ID: "))
    Name = input("Enter Patient Name: ")
    Age = int(input("Enter Age: "))
    Gender = input("Enter Gender: ")

    if Age >= 18:
        print("\nPatient Registration Successful")
        print("Patient ID:", patient_id)
        print("Name:", Name)
        print("Age:", Age)
        print("Gender:", Gender)
    else:
        print("\nPatient is below 18 years")
        print("Parent/Guardian details are required")


# --- DOCTORS DATABASE ---

def doctors_database():
    doctors = [
        {"Name": "Dr.Arun", "Specialty": "Cardiologist", "Available": True},
        {"Name": "Dr.John", "Specialty": "Neurologist", "Available": True},
        {"Name": "Dr.Adams", "Specialty": "Dermatologist", "Available": True},
        {"Name": "Dr.Priya", "Specialty": "Gynecologist", "Available": True},
        {"Name": "Dr.Priyan", "Specialty": "Cardiologist", "Available": True},
        {"Name": "Dr.Jeno", "Specialty": "Dermatologist", "Available": True}
    ]
    return doctors


# --- VIEW DOCTORS ---

def view_doctors():
    specialization = input("Enter Specialization: ")

    print("\nAvailable Doctors:")

    found = False
    for doctor in doctors_database():
        if doctor["Specialty"] == specialization and doctor["Available"]:
            print("Name:", doctor["Name"])
            print("Specialty:", doctor["Specialty"])
            print()
            found = True

    if not found:
        print("No doctor available.")


# --- BOOK APPOINTMENT ---

def book_appointment():
    Specialty = input("Enter Doctor Specialty: ")
    Doctor_name = input("Enter Doctor Name: ")

    for doctor in doctors_database():
        if doctor["Specialty"] == Specialty and doctor["Name"] == Doctor_name:
            if doctor["Available"]:
                print("Appointment Booked with", doctor["Name"])
            else:
                print(doctor["Name"], "is not available")
            return

    print("Doctor not found.")


# --- GENERATE BILL ---

def generate_bill():
    Consultation_Fee = int(input("Enter Consultation Fee: "))
    Treatment_Fee = int(input("Enter Treatment Fee: "))

    Total = Consultation_Fee + Treatment_Fee

    print("\nHospital Bill")
    print("Consultation Fee:", Consultation_Fee)
    print("Treatment Fee:", Treatment_Fee)
    print("Total:", Total)


# --- PATIENT HISTORY ---

def patient_history():
    history = {}

    history["Patient_ID"] = input("Enter Patient ID: ")
    history["Patient_Name"] = input("Enter Patient Name: ")
    history["Disease"] = input("Enter Disease: ")
    history["Treatment"] = input("Enter Treatment: ")
    history["Medicine"] = input("Enter Medicine: ")

    print("\nPatient Medical History")
    print("Patient ID:", history["Patient_ID"])
    print("Patient Name:", history["Patient_Name"])
    print("Disease:", history["Disease"])
    print("Treatment:", history["Treatment"])
    print("Medicine:", history["Medicine"])


# --- MAIN MENU ---

while True:

    print("\n===== Hospital Management System =====")
    print("1. Patient Registration")
    print("2. View Doctors")
    print("3. Book Appointment")
    print("4. Generate Bill")
    print("5. Patient Medical History")
    print("6. Exit")

    choice = int(input("Enter your choice: "))

    if choice == 1:
        patient_registration()

    elif choice == 2:
        view_doctors()

    elif choice == 3:
        book_appointment()

    elif choice == 4:
        generate_bill()

    elif choice == 5:
        patient_history()

    elif choice == 6:
        print("Thank you for using Hospital Management System.")
        break

    else:
        print("Invalid Choice")