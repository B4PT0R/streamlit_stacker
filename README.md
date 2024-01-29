
# streamlit_stacker

streamlit_stacker is a python package implementing a main st_stacker class.
This class can be used with similar syntax as the streamlit module but the attribute calls will be stacked in a list (the stack) instead of being resolved. A simple call to the refresh() method will deal with rendering (=actually execute the corresponding streamlit commands of) the whole stack on demand.

Populating a stack with attribute calls, context mangers and callbacks thus becomes similar to setting up a gui layout in an object oriented manner.

On top of being added to the stack, all st_stacker attribute calls will return one or several st_output objects. These are meant to be placeholder objects anticipating the reception of actual outputs returned by streamlit attribute calls when they will get executed. 

The .value property will get actualized in real time as soon as the corresponding streamlit widgets have a non-empty state.

This module is very useful to implement stateful and/or dynamic execution of streamlit commands in an interactive web interface.

It is meant to support all streamlit commands and syntaxes allowed by the streamlit module. If not, feel free to report an issue, we'll work on it :).

## Installation

```bash
$ pip install streamlit-stacker
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
