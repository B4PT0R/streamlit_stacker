
# streamlit_stacker

streamlit_stacker is a python package implementing a main st_stacker class.
This class can be used with similar syntax as the streamlit module but the calls to commands will be stacked and rendered latter in a controlable manner.

Useful to implement dynamic execution of streamlit commands in an interactive console interface.
Supports (almost) all streamlit methods

## Installation

```bash
$ pip install streamlit_stacker
```

## Usage

```python
import streamlit as st
from streamlit_stacker import st_stacker

#shortcut
state=st.session_state

#define the stacker in state
if not 'stacker' in state:
    state.stacker=st_stacker()
stk=state.stacker

#resets all commands in the stacker to a non-rendered state, so that the next call to refresh will render them again
stk.reset()

if not 'test' in state:
    #stack a chat message and a button in a container, won't be rendered immediately
    state.c=stk.container()
    with state.c:
        with stk.chat_message(name='user'):
            stk.write("Hello!")
            
    #callback to add a new message when the button is clicked
    def on_click():
        with state.c:
            with stk.chat_message(name='user'):
                stk.write("Hello again!")

    stk.button("click me!",on_click=on_click)
    state.test=True

#render the stack: the chat message and the button will appear on screen on every rerun, even though the corresponding commands have been called only once at first run
#every click on the button will add another chat message to the container
stk.refresh()
```

## License

This project is licensed. Please see the LICENSE file for more details.

## Contributions

Contributions are welcome. Please open an issue or a pull request to suggest changes or additions.

## Contact

For any questions or support requests, please contact Baptiste Ferrand at the following address: bferrand.maths@gmail.com.
