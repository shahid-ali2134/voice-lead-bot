# routes/leads.py

class LeadQualification:
    def __init__(self):
        self.state = "start"
        self.lead_data = {}

    def next_prompt(self, user_input: str = None) -> str:
        if self.state == "start":
            self.state = "ask_name"
            return "Hi there! May I know your name?"

        elif self.state == "ask_name":
            self.lead_data["name"] = user_input
            self.state = "ask_company"
            return f"Nice to meet you {user_input}! Which company are you representing?"

        elif self.state == "ask_company":
            self.lead_data["company"] = user_input
            self.state = "ask_budget"
            return "Got it. What's your estimated budget for this project or service?"

        elif self.state == "ask_budget":
            self.lead_data["budget"] = user_input
            self.state = "ask_interest"
            return "Great. Could you tell me briefly what service you're interested in?"

        elif self.state == "ask_interest":
            self.lead_data["interest"] = user_input
            self.state = "qualified"
            return (f"Thanks {self.lead_data['name']}! "
                    f"I’ve noted your interest in {self.lead_data['interest']} "
                    f"with a budget of {self.lead_data['budget']}. A sales rep will follow up shortly.")

        elif self.state == "qualified":
            return "I already have your information. Would you like me to connect you with our team?"

    def is_qualified(self) -> bool:
        return self.state == "qualified"

    def get_lead_data(self) -> dict:
        return self.lead_data
