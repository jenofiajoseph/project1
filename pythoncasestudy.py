#HOSPITAL MANAGEMENT SYSTEM

#ADD PATIENT

def patient_registration():
    patient_id=input("Enter the patient ID:")
    Name=input("Enter the patient name:")
    Age=int(input("Enter Age:"))
    Gender=input("Enter Gender:")
    if Age>=18:
        print("Patient registration successfully")
        print("Patient_id:",patient_id)
        print("Name:",Name)
        print("Age:",Age)
        print("gender:",Gender)
    else:
        print("Patient is below 18 years") 
        print("Parent/Gaurdian details are required") 

patient_registration()

# Doctors are available with specific specialization:
    
def doctors_database():
    doctors = [
        {"Name": "Dr.Arun", "Specialty": "Cardiologist", "Available": True},
        {"Name": "Dr.John", "Specialty": "Neurologist", "Available": True},
        {"Name": "Dr.Adams", "Specialty": "Dermatologist", "Available": True},
        {"Name": "Dr.Priya", "Specialty": "Gynecologist", "Available": True},
        {"Name": "Dr.Priyan", "Specialty": "Cardiologist", "Available": True},
        {"Name": "Dr.Jeno", "Specialty": "Dermatologist", "Available": True}
    ]

    specialization = input("Enter Specialization: ")

    print("Available Doctors:")

    for doctor in doctors:
        if doctor["Specialty"] == specialization and doctor["Available"]:
            print("Name:", doctor["Name"])
            print("Specialty:", doctor["Specialty"])

    return doctors


#appointments are assigned based on doctors availability:

def book_appointment():
    Specialty = input("Enter Doctor Specialty:")
    Doctor_name=input("Enter Doctor Name:")
    for doctor in doctors_database():
        if doctor["Specialty"] == Specialty and doctor["Name"]==Doctor_name:
            if doctor["Available"]:
                print("Appointment Booked with", doctor["Name"])
            else:
                print(doctor["Name"], "is not available")

book_appointment()               

#Bills are Generated for consultations and treatments

def generate_bill():
    Consultation_Fee=500
    Treatment_Fee=int(input("Enter Treatment Fee:"))
    Total=Consultation_Fee+Treatment_Fee
    print("Hospital Bill:")
    print("Consultation_Fee:",Consultation_Fee)
    print("Treatment_Fee:",Treatment_Fee)
    print("Total:",Total)

generate_bill()

#Patient medical history is stored and managed

def patient_history():
    history={}
    history["Patient_ID"]=input("Enter patient ID:")
    history["Patient_Name"]=input("Enter patient Name:")
    history["Disease"]=input("Enter patient Disease:")
    history["Treatment"]=input("Enter Treatment:")
    history["Medicine"]=input("Enter Medicine:")

    print("\nPATIENT MEDICAL HISTORY")
    print("Patient ID:", history["Patient_ID"])
    print("Patient Name:", history["Patient_Name"])
    print("Disease:", history["Disease"])
    print("Treatment:", history["Treatment"])
    print("Medicine:", history["Medicine"])

patient_history()

while True:
    print("\n===== Hospital Management System =====")
    print("1. Patient Registration")
    print("2. Doctors database")
    print("3. Book Appointment")
    print("4. Generate Bill")
    print("5. Patient Medical History")
    print("6. Exit")

    choice = int(input("Enter your choice: "))

    if choice == 1:
        patient_registration()

    elif choice == 2:
        doctors_database()

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