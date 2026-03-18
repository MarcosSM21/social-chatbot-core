class ResponseEngine:
    def generate_response(self, message:str) -> str:
        cleaned_message = message.strip()

        if not cleaned_message:
            return "No he recibido ningín mensaje. Por favor, envíame algo para que pueda ayudarte." 
        
        return f"Has dicho: {cleaned_message}"
    

