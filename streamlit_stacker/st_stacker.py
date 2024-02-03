import os
_root_=os.path.dirname(os.path.abspath(__file__))
import sys
if not sys.path[0]==_root_:
    sys.path.insert(0,_root_)
def root_join(*args):
    return os.path.join(_root_,*args)

import streamlit as st
import time
# Imports custom components and a mapping of streamlit methods/attributes onto the appropriate stacked version
from components import COMPONENTS,ATTRIBUTES_MAPPING
#Specificaly deals with st.echo
from echo import echo_generator
from streamlit.errors import DuplicateWidgetID
from contextlib import contextmanager
import logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)

def split_dict(mydict,keys):
    d1={}
    d2={}
    for key in mydict:
        if key in keys:
            d1[key]=mydict[key]
        else:
            d2[key]=mydict[key]
    return d1,d2

def inspect_key(name,key):
    from inspect import getfullargspec
    try:
        return key in getfullargspec(st_map(name))[0]
    except:
        return False

def instantiate(class_name, *args, **kwargs):
    cls = globals()[class_name] 
    return cls(*args, **kwargs)

def isiterable(obj):
    try:
        it=iter(obj)
    except:
        return False
    else:
        if isinstance(obj,str):
            return False
        else:
            return True

class NoContext:
    def __init__(self):
        pass
    def __enter__(self,*args,**kwargs):
        pass
    def __exit__(self,*args,**kwargs):
        pass

class KeyManager:
# A simple widget key manager
    def __init__(self):
        self.keys=[]

    def gen_key(self):
        i=0
        while ((key:='key_'+str(i)) in self.keys):
            i+=1
        self.keys.append(key)
        return key
    
    def dispose(self,key):
        if key in self.keys:
            self.keys.remove(key)

def st_map(attr):
# Maps attributes keys to streamlit built-in or custom components objects
        try:
            return getattr(st,attr)
        except:
            if attr in COMPONENTS:
                return COMPONENTS[attr]
            else:
                raise Exception(f"Unknown streamlit attribute: {attr}")

@contextmanager
def ctx(context):
# Context manager to open/close streamlit objects as context for others at rendering time
    if not context==None:
        if isinstance(context,(st_callable,st_one_shot_callable)):
            with st_map(context.name)(*context.args,**context.kwargs):
                yield
        elif isinstance(context,(st_output,st_property,st_direct_callable)):
            if not context.value is None:
                with context.value:
                    yield
            else:
                with NoContext():
                    yield
        else:
            with NoContext():
                yield
    else:
        with NoContext():
            yield

def render(callable):
# Renders stacked widgets by calling streamlit / third party components and captures outputs if any
    results=st_map(callable.name)(*callable.args,**callable.kwargs)
    if 'key' in callable.kwargs:
        key=callable.kwargs['key']
    else:
        key=None
    
    if not results is None:
        if isiterable(results):
            for i,result in enumerate(results):
                if i<len(callable.outputs):
                    callable.outputs[i]._value=result
                    callable.outputs[i].key=key
        else:
            callable.outputs[0]._value=results
            callable.outputs[0].key=key

class st_object:
# Base class for stacked version of streamlit objects
# Makes them usable as context managers for other objects
    def __init__(self,stacker,context=None):
        self.stacker=stacker
        self.context=context

    def __enter__(self):
        self.context = self.stacker.current_context
        self.stacker.current_context = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stacker.current_context = self.context

class st_renderable(st_object):
# Base class for objects that need rendering
    def __init__(self,stacker,name,context=None):
        st_object.__init__(self,stacker,context)
        self.name=name
        self.has_rendered=False
        self.tag=name
        self.key=None

    def render(self):
        if not self.has_rendered:
            with ctx(self.context):
                render(self)
            self.has_rendered=True

class st_callable(st_renderable):
# For most common callable objects like st.write, st.button, st.text_input...
    def __init__(self,stacker,name,context=None):
        st_renderable.__init__(self,stacker,name,context)
        self.iter_counter=0
        self.args=None
        self.kwargs=None
        self.outputs=[]

    def __call__(self,*args,**kwargs):
        self.args=args
        if 'tag' in kwargs:
            d,kwargs=split_dict(kwargs,['tag'])
            self.tag=d['tag']
        if inspect_key(self.name,'key') and not self.name=='form':
            if not 'key' in kwargs:
                key=self.stacker.gen_key()
                self.key=key
                kwargs.update({'key':key})
            else:
                self.key=kwargs['key']
        elif self.name=='form':
            #create a unique key for the form and pass it as arg
            key=self.stacker.gen_key()
            self.key=key
            kwargs={}
            self.args=(key,)

        self.kwargs=kwargs
        obj=st_output(stacker=self.stacker,context=self.context,call_name=self.name,call_args=self.args,call_kwargs=self.kwargs)
        self.outputs.append(obj)
        self.stacker.append(self) #An object is appended to the pile only when all information required to render it and route its outputs is available
        return obj

class st_unpackable_callable(st_renderable):
    # For unpackable objects like st.columns, st.tabs...
    def __init__(self,stacker,name,context=None):
        st_renderable.__init__(self,stacker,name,context)
        self.iter_counter=0
        self.args=None
        self.kwargs=None
        self.outputs=[]

    def __call__(self,*args,**kwargs):
        self.args=args
        if 'tag' in kwargs:
            d,kwargs=split_dict(kwargs,['tag'])
            self.tag=d['tag']
        if inspect_key(self.name,'key'):
            if not 'key' in kwargs:
                key=self.stacker.gen_key()
                self.key=key
                kwargs.update({'key':key})
            else:
                self.key=kwargs['key']
        self.kwargs=kwargs
        return self

    def __iter__(self):
        return self

    def __next__(self):
        if self.iter_counter<len(self):
            obj=st_output(stacker=self.stacker,context=self.context,call_name=self.name,call_args=self.args,call_kwargs=self.kwargs)
            self.outputs.append(obj)
            self.iter_counter+=1
            return obj 
        else:
            self.iter_counter=0
            self.stacker.append(self) #An object is appended to the pile only when all information required to render it and route its outputs is available
            raise StopIteration   

    def __len__(self):
        if isinstance(self.args[0],int) and self.args[0]>1:
            return self.args[0]
        elif isiterable(self.args[0]) and len(self.args[0])>1:
            return len(self.args[0])
        else:
            return 1

class st_output(st_object):
    # Placeholder object for outputs of callables
    def __init__(self,stacker,context,call_name=None,call_args=None,call_kwargs=None):
        st_object.__init__(self,stacker,context)
        self._value=None
        self.key=None
        self.call_kwargs=call_kwargs
        self.call_args=call_args
        self.call_name=call_name

    def __getattr__(self,attr):
        if attr in ATTRIBUTES_MAPPING:
            obj=instantiate(ATTRIBUTES_MAPPING[attr],self.stacker,attr,context=self)
            self.stacker.append(obj)
            return obj
        else:
            raise AttributeError(f"Unsupported attribute: {attr}")

    @property    
    def value(self):
        if not self.key is None:
            if not st.session_state[self.key] is None:
                return st.session_state[self.key]
            else:
                return self._value
        else:
            return self._value
        
    def __repr__(self):
        kwargs_string=','.join(f"{key}={repr(value)}" for key,value in self.call_kwargs.items())
        args_string=','.join(f'{repr(arg)}' for arg in self.call_args)
        return f"st_output(name={repr(self.call_name)},args=({args_string}),kwargs={{{kwargs_string}}})"


class st_property(st_renderable):
    # For property-like objects such as st.sidebar
    def __init__(self,stacker,name,context=None):
        st_renderable.__init__(self,stacker,name,context)
        self.value=None
        self.item=None
        self.stacker.append(self)

    def __getattr__(self,attr):
        if attr in ATTRIBUTES_MAPPING:
            obj=instantiate(ATTRIBUTES_MAPPING[attr],self.stacker,attr,context=self)
            return obj
        else:
            raise AttributeError

    def render(self):
        with ctx(self.context):
            self.value=st_map(self.name)

class st_one_shot_callable(st_renderable):
    # For callables that need to be rendered only once
    # such as st.balloons, st.snow...
    def __init__(self,stacker,name,context=None):
        st_renderable.__init__(self,stacker,name,context)
        self.outputs=[]


    def __call__(self,*args,**kwargs):
        self.args=args
        self.kwargs=kwargs
        obj=st_output(stacker=self.stacker,context=self.context,call_name=self.name,call_args=self.args,call_kwargs=self.kwargs)
        self.outputs.append(obj)
        self.stacker.append(self)
        return obj

    def render(self):
        super().render()
        self.stacker.remove(self)


class st_direct_callable:
    # Resolves streamlit call directly without appending to the stack
    # useful for st.spinner, st.progress. st.balloons st.snow (optional delay to let the animation finish before the next rerun)
    def __init__(self,stacker,name,context):
        self.stacker=stacker
        self.name=name
        self.context=context
        self.value=None
        self.delay=0

    def __call__(self,*args,**kwargs):
        with ctx(self.context):
            self.value=st_map(self.name)(*args,**kwargs)
        time.sleep(self.delay)
        return self.value
       


def st_direct_property(stacker,name,context):
    # Returns a streamlit property directly without appending to the stack
    # Useful for st.column_config, st.session_state...
    with ctx(context):
        value=st_map(name)
    return value    


class st_balloons(st_direct_callable):
    
    def __init__(self,stacker,name,context=None):
        st_direct_callable.__init__(self,stacker,name,context)
        self.delay=2

class st_snow(st_direct_callable):
    
    def __init__(self,stacker,name,context=None):
        st_direct_callable.__init__(self,stacker,name,context)
        self.delay=7       


class st_stacker:
    """
    Main class, mimicking the streamlit module behaviour in a stacked manner  
    Wraps streamlit attrs into stacked versions
    Holds pile/stack of stacked objects
    Renders all objects in the stack on call to refresh, or streams them one by one in real-time from the pile
    Keeps the current context required for widget rendering 
    """

    def __init__(self,key_manager=None,mode='static'):
        if key_manager==None:
            self.key_manager=KeyManager()
        else:
            self.key_manager=key_manager
        self.mode=mode
        self.stack=[]
        self.hidden_tags=[]
        self.current_context=None
        self.echo=echo_generator(self)
        self.secrets=None
    
    def hide(self,tag):
        if not tag in self.hidden_tags:
            self.hidden_tags.append(tag)

    def show(self,tag):
        if tag in self.hidden_tags:
            self.hidden_tags.remove(tag)

    def gen_key(self):
        return self.key_manager.gen_key()

    def __getattr__(self,attr):
        #instantiate the adequate st_object subtype corresponding to the attribute according to ATTRIBUTES_MAPPING
        #Refer to the components.py module to see how ATTRIBUTES_MAPPING is defined
        if attr in ATTRIBUTES_MAPPING:
            obj=instantiate(ATTRIBUTES_MAPPING[attr],self,attr,context=self.current_context)
            return obj #The object itself will deal with its appending to the stack once all information required to render it is available (such as call arguments, outputs etc...)
        else:
            raise AttributeError

    def append(self,obj):
        #appends an object to the stack, render it immediately in streamed mode
        if self.mode=='streamed':
            self.refresh()
            self.render(obj)
        self.stack.append(obj)
        
    def render(self,obj):
        if not obj.has_rendered and not obj.tag in self.hidden_tags:
            try:
                obj.render()
            except DuplicateWidgetID:
                #Some widgets take several mainloop turns to be consumed by streamlit and leave screen
                #This avoids to attempt rerendering them while they are still active  
                pass


    def remove(self,obj):
        """
        removes an object from the stack (useful for st_one_shot_callable objects)
        """
        if obj in self.stack:
            self.stack.remove(obj)


    def refresh(self):
        """
        renders every object in the stack (to refresh the whole app display).
        """
        for obj in self.stack:
            self.render(obj)
            

    def reset(self):
        """
        Supposed to be called at the beginning of the streamlit main app script (understood as the mainloop of the app)
        widgets need to be rendered every turn of the mainloop, otherwise these widgets will disappear from the app's display.
        This resets all objects in the stack to a non-rendered state so that the next call to refresh will render them all again
        """
        for obj in self.stack:
            obj.has_rendered=False

    def clear(self):
        """
        clears the whole stack
        """
        self.stack.clear()
