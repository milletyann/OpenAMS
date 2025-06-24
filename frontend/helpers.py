########################
### HELPER FUNCTIONS ###
########################

def clip_text(text, thres):
    if not text:
        return ""
    return text if len(text) < thres else text[:thres] + "..."