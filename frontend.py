import streamlit as st
from backend import use_model

# Make the app wider
st.set_page_config(
    layout="wide",
    page_title="The Eccentric Tavern",
    page_icon="🪑"
)



#initialize chat history and itext box
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_provider" not in st.session_state:
    st.session_state.last_provider = "GPT 4o"

if "last_personality" not in st.session_state:
    st.session_state.last_personality = "🎩 Trusty butler"

if "input" not in st.session_state:
    st.session_state.input = ""

if "clear_input" not in st.session_state:
    st.session_state.clear_input = False

if "waiting_for_response" not in st.session_state:
    st.session_state.waiting_for_response = False

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = ""

# Clear input if flag is set
if st.session_state.clear_input:
    st.session_state.input = ""
    st.session_state.clear_input = False

 

    
# Chat history spans columns 1 and 2
col1, col2_3 = st.columns([1, 3])

with col1:
    st.title ("The Eccentric Tavern")
    st.write("You walk into a small, cozy tavern on a chilly winter night and sit down on a bench by the fireplace...")
    st.write("") #add vertical spacing
    st.write("")
    
    personality = st.selectbox("Choose a character to chat with:",
     ["🎩 Trusty butler", "⚓️ Pirate", "👱🏻‍♀️ Sorority girl"])

    provider = st.selectbox("Choose a model:", ["Mistral Small 3.2","GPT 4o", "DeepSeek V3.1", "Grok 4"])

    image_upload = st.file_uploader("", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'heic', 'csv', 'xlsx', 'xls', 'docx', 'pdf'])


with col2_3:
    # Chat history in scrollable container (always visible)
    chat_container = st.container(height=630)
    with chat_container:
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.chat_message("user", avatar="👨🏻‍💻").write(msg['content'])
                else:
                    if st.session_state.last_personality == "🎩 Trusty butler":
                        st.chat_message("assistant", avatar="🎩").write(f"{msg['content']}")
                    elif st.session_state.last_personality == "⚓️ Pirate":
                        st.chat_message("assistant", avatar="⚓️").write(f"{msg['content']}")
                    elif st.session_state.last_personality == "👱🏻‍♀️ Sorority girl":
                        st.chat_message("assistant", avatar="👱🏻‍♀️").write(f"{msg['content']}")
        else:
            # Show placeholder image when chat history is empty
            st.markdown("<br><br><br><br>", unsafe_allow_html=True)  # Add vertical spacing
            image_col1, image_col2, image_col3 = st.columns([1, 1.2, 1])
            with image_col2:
                st.image("tavern.png", 
                        caption="", 
                        width=500, 
                        use_container_width=True)
        
        # Streaming response placeholder inside the chat container
        if st.session_state.waiting_for_response:
            st.session_state.streaming_placeholder = st.empty()
    
    #prompt box and talk button
    col1, col2 = st.columns([6, 1])
    
    with col1:
        prompt = st.text_input("", key="input", autocomplete="off", label_visibility="collapsed",  placeholder= "Say something...")

    with col2:
        talk_button = st.button("Talk", use_container_width=True)

   



# --- Reset chat and history if toggles change ---
if (
    provider != st.session_state.last_provider
    or personality != st.session_state.last_personality
):
    st.session_state.chat_history = []  
    st.session_state.last_provider = provider
    st.session_state.last_personality = personality
    st.rerun()

# Handle waiting for response
if st.session_state.waiting_for_response:
    # Add placeholder for assistant response
    if len(st.session_state.chat_history) == 0 or st.session_state.chat_history[-1]["role"] != "assistant" or st.session_state.chat_history[-1]["content"] != "":
        st.session_state.chat_history.append({"role": "assistant", "content": ""})
    
    # Stream the response
    full_response = ""
    
    for chunk in use_model(
        st.session_state.pending_prompt,
        image_upload,
        st.session_state.chat_history[:-2],  # Pass history without the user message and empty assistant message
        provider=provider,
        personality=personality,
    ):
        full_response += chunk
        # Display the streaming response in the placeholder inside chat container
        if hasattr(st.session_state, 'streaming_placeholder'):
            with st.session_state.streaming_placeholder.container():
                if personality == "🎩 Trusty butler":
                    st.chat_message("assistant", avatar="🎩").write(full_response)
                elif personality == "⚓️ Pirate":
                    st.chat_message("assistant", avatar="⚓️").write(full_response)
                elif personality == "👱🏻‍♀️ Sorority girl":
                    st.chat_message("assistant", avatar="👱🏻‍♀️").write(full_response)
    
    # Update the final response in chat history
    st.session_state.chat_history[-1]["content"] = full_response
    st.session_state.waiting_for_response = False
    st.session_state.pending_prompt = ""
    st.rerun()

#talk by pressing return or talk button
if prompt or talk_button:
    # Add user message to chat history immediately
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.session_state.clear_input = True
    st.session_state.waiting_for_response = True
    st.session_state.pending_prompt = prompt
    st.rerun()

