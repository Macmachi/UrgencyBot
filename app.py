'''
### PROJECT INFO ####
# Project name: UrgencyBot   
# Project and code author: Arnaud R.
# Version 1.0
# This project is a test of GPT4's medical features and should not be used for real use cases!
DOCUMENTATION & Credits####
* Open AI: https://platform.openai.com/docs/api-reference 
* Huggingface : https://huggingface.co/docs/hub/spaces-embed
* Thanks to ysharma for his example of the stream function of the GPT4 api on HuggingFace : https://huggingface.co/spaces/ysharma/ChatGPT4 & aliabid94 for his gradio theme !
### NICE-TO-HAVE FEATURES ####
* Have profile management or else a more pro active not that asks questions like "What is your problem?
  (Currently you can use long_term_memory manually or tell it vocally as it has a memory)
BUGS and change to be made ####
* Put the open AI key in the environment
'''
import gradio as gr
import os 
import json 
import requests
#Does not work in Gradio but can be uncommented for local execution (look for tiktoken terms to uncomment the rest of the code needed)
#import tiktoken
#enc = tiktoken.encoding_for_model("gpt-4")

# streaming endpoint 
API_URL = "https://api.openai.com/v1/chat/completions" 
# !!! Put your key for the openAI api here !!!
OPENAI_API_KEY = ""

#def count_prompt_tokens_with_tiktoken(text):
    #tokens = enc.encode(text)
    #return len(tokens)

# inference function
def predict(system_msg, inputs, top_p, temperature, maxtokens, chat_counter, chatbot=[], history=[]):  
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    print(f"system message is : {system_msg}")
    # we should not pass in as we define a default variable for system_msg
    if system_msg.strip() == '':
        initial_message = [{"role": "user", "content": f"{inputs}"},]
        multi_turn_message = []
    else:
        initial_message= [{"role": "system", "content": system_msg},
                   {"role": "user", "content": f"{inputs}"},]
        multi_turn_message = [{"role": "system", "content": system_msg},]

    # Calculate tokens in the initial_message
    '''
    total_prompt_tokens = sum([count_prompt_tokens_with_tiktoken(m['content']) for m in initial_message])
    prompt_cost_per_token = 0.03 / 1000  # Coût par token
    total_cost_prompt = total_prompt_tokens * prompt_cost_per_token  # Coût total     
    print(f"Total prompt tokens (estimation) : {total_prompt_tokens} (= {total_cost_prompt:.4f}$)") 
    '''
    if chat_counter == 0 :
        payload = {
        "model": "gpt-4",
        "messages": initial_message , 
        "max_tokens": maxtokens, #2000
        "temperature" : 0.5,
        "top_p":1.0,
        "n" : 1,
        "stream": True,
        "presence_penalty":0,
        "frequency_penalty":0,
        }
        print(f"chat_counter - {chat_counter}")
    # if chat_counter != 0 :
    else: 
        # Type of - [{"role" : "system", "content" : system_msg},]
        messages=multi_turn_message 
        for data in chatbot:
          user = {}
          user["role"] = "user" 
          user["content"] = data[0] 
          assistant = {}
          assistant["role"] = "assistant" 
          assistant["content"] = data[1]
          messages.append(user)
          messages.append(assistant)
        temp = {}
        temp["role"] = "user" 
        temp["content"] = inputs
        messages.append(temp)

        # messages
        payload = {
        "model": "gpt-4",
        "messages": messages,  
        "max_tokens": maxtokens, #2000
        "temperature" : temperature, #0.5,
        "top_p": top_p, #1.0,
        "n" : 1,
        "stream": True,
        "presence_penalty":0,
        "frequency_penalty":0,}

        # Calculate tokens in the chat history
        ''' 
        total_prompt_tokens = sum([count_prompt_tokens_with_tiktoken(m['content']) for m in messages])
        prompt_cost_per_token = 0.03 / 1000  # Coût par token
        total_cost_prompt = total_prompt_tokens * prompt_cost_per_token  # Coût total     
        print(f"Total prompt tokens (estimation) : {total_prompt_tokens} (= {total_cost_prompt:.4f}$)") 
        '''
    chat_counter+=1

    history.append(inputs)
    print(f"Logging : payload is - {payload}")
    # make a POST request to the API endpoint using the requests.post method, passing stream=True
    response = requests.post(API_URL, headers=headers, json=payload, stream=True)
    print(f"Logging : response code - {response}")
    token_counter = 0 
    partial_words = "" 
    counter=0
    for chunk in response.iter_lines():
        # the first piece to skip
        if counter == 0:
          counter+=1
          continue
        # check that each line is not empty
        if chunk.decode() :
          chunk = chunk.decode()
          # decode each line, the answer data being expressed in bytes
          if len(chunk) > 12 and "content" in json.loads(chunk[6:])['choices'][0]['delta']:
              partial_words = partial_words + json.loads(chunk[6:])['choices'][0]["delta"]["content"]
              if token_counter == 0:
                history.append(" " + partial_words)
              else:
                history[-1] = partial_words
              # convert to tuples of the list
              chat = [(history[i], history[i + 1]) for i in range(0, len(history) - 1, 2) ]  
              token_counter+=1
        
              # gather {chatbot: chat, state: history}
              yield chat, history, chat_counter, response 
 
    completion_cost_per_token = 0.06 / 1000  # Coût par token
    total_cost = token_counter * completion_cost_per_token  # Coût total     
    print(f"Total completion tokens : {token_counter} (= {total_cost:.4f}$)")          
              
# reset
def reset_textbox():
    return gr.update(value='')

# function to reset chat history, user input and chatbot
def reset_all():
    return [], '', 0, []

# to define a component as visible=False
def set_visible_false():
    return gr.update(visible=False)

# to define a component as visible=True
def set_visible_true():
    return gr.update(visible=True)

title = """<h1 align="center">🏥 UrgencyBot</h1>"""
instruction = """<h3 align="center">Instruction : Duplicate this space and add your key in app.py ! </h3>"""
subtile = """<h3 align="center">WARNING : This project is a test of GPT4's medical features and should not be used for real use cases!</h3>"""

# use info to add additional information about the system message in GPT4
system_msg_info = """Default: You are a medical advisor who must respond to medical problems only and you must tell me if it is useful to go see a doctor or go to the emergency room if it is serious."""

# modify the existing Gradio theme
with gr.Blocks(theme='aliabid94/new-theme') as demo:

    gr.HTML(title)
    gr.HTML(instruction)
    gr.HTML(subtile)

    with gr.Column(elem_id = "col_container"):
        chatbot = gr.Chatbot(label='TedCare', elem_id="chatbot")
        inputs = gr.Textbox(placeholder= "Enter your medical condition or symptoms", label= "Click [Enter] or Send to send your message")
        state = gr.State([])  # type: ignore
        with gr.Row():
            with gr.Column(scale=3):  
                reset_button = gr.Button("Erase my memory")

            with gr.Column(scale=3):
                b1 = gr.Button("Send")

        with gr.Accordion(label="Instructions to the IA agent", open=False):
            system_msg = gr.Textbox(label="Instructions to the IA agent :", info = system_msg_info, value="")
        if system_msg.value == "":
            system_msg.value = "You are a medical advisor who must respond to medical problems only and you must tell me if it is useful to go to a doctor or to the emergency room if it is serious."

        # top_p, temperature # max_tokens #server_status_code
        with gr.Accordion("Parameters", open=False):
            top_p = gr.Slider( minimum=-0, maximum=1.0, value=1.0, step=0.05, interactive=True, label="Top-p (core sampling)",)
            temperature = gr.Slider( minimum=-0, maximum=5.0, value=0.5, step=0.1, interactive=True, label="Temperature",)
            maxtokens = gr.Slider( minimum=-100, maximum=8000, value=2000, step=100, interactive=True, label="Maximum tokens",)
            server_status_code = gr.Textbox(label="OpenAI server status", )
            chat_counter = gr.Number(value=0, visible=False, precision=0)

        with gr.Row():
            toggle_dark = gr.Button(value="Light/Dark").style(full_width=False)
        
    # event management
    inputs.submit( predict, [system_msg, inputs, top_p, temperature, maxtokens, chat_counter, chatbot, state], [chatbot, state, chat_counter, server_status_code],)  
    b1.click( predict, [system_msg, inputs, top_p, temperature, maxtokens, chat_counter, chatbot, state], [chatbot, state, chat_counter, server_status_code],)  
    
    inputs.submit(set_visible_false, [], [system_msg])
    b1.click(set_visible_false, [], [system_msg])
    
    # associate this function with the reset button
    reset_button.click(reset_all, outputs=[state, inputs, chat_counter, chatbot])


    b1.click(reset_textbox, [], [inputs])
    inputs.submit(reset_textbox, [], [inputs])

    toggle_dark.click(None, _js="""() => { document.body.classList.toggle('dark'); } """)
        
demo.queue(max_size=99, concurrency_count=20).launch(debug=True)