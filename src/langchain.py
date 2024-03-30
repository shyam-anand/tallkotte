from langchain.llms import OpenAIChat
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain import LLMChain, PromptTemplate


def main(resume: str):
    template = """Format the provided resume to this YAML template:
          ---
      name: ''
      phoneNumbers:
      - ''
      websites:
      - ''
      emails:
      - ''
      dateOfBirth: ''
      addresses:
      - street: ''
        city: ''
        state: ''
        zip: ''
        country: ''
      summary: ''
      education:
      - school: ''
        degree: ''
        fieldOfStudy: ''
        startDate: ''
        endDate: ''
      workExperience:
      - company: ''
        position: ''
        startDate: ''
        endDate: ''
      skills:
      - name: ''
      certifications:
      - name: ''

      {chat_history}
      {human_input}"""

    prompt = PromptTemplate(
        input_variables=["chat_history", "human_input"],
        template=template)

    memory = ConversationBufferMemory(memory_key="chat_history")

    llm_chain = LLMChain(
        llm=OpenAIChat(model="gpt-3.5-turbo"),
        prompt=prompt,
        verbose=True,
        memory=memory,
    )

    res = llm_chain.predict(human_input=resume)
    return res


if __name__ == '__main__':
    main()
