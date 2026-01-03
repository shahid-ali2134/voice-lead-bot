# routes/leads.py

class LeadQualification:
    def __init__(self, mode: str = "bye"):
        """
        mode:
          - "bye"      -> wrap up and end naturally
          - "continue" -> after qualification, keep chatting/helping
        """
        self.state = "start"
        self.lead_data = {}
        self.mode = mode

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

            # ✅ move to a post-qualified state
            self.state = "handoff"

            name = self.lead_data.get("name", "there")
            interest = self.lead_data.get("interest", "your request")
            budget = self.lead_data.get("budget", "your budget")

            if self.mode == "continue":
                return (
                    f"Thanks {name}! I’ve noted your interest in {interest} with a budget of {budget}. "
                    f"Before I connect you with a sales rep, is there anything else you’d like to add—"
                    f"like timeline, preferred tech stack, or key features?"
                )

            # default = bye
            return (
                f"Thanks {name}! I’ve noted your interest in {interest} with a budget of {budget}. "
                f"A sales rep will follow up shortly. Have a great day — bye!"
            )

        elif self.state == "handoff":
            # If you chose continue mode, you can respond naturally here without breaking the lead flow.
            if self.mode == "continue":
                # Keep it simple and safe: acknowledge + offer next step
                return "Got it — thank you. I’ll pass that along to the team. Anything else before we wrap up?"

            # If bye mode, keep it short and end
            return "Thanks again — bye!"

        return "Sorry, I didn’t catch that."

    def is_qualified(self) -> bool:
        # ✅ treat handoff as “lead captured”
        return self.state in ("handoff",)

    def get_lead_data(self) -> dict:
        return self.lead_data
