from functools import partial
from copy import deepcopy
import inspect


VALID_INFORMATION = {
    'data_object': {'namespaces', 'attributes', 'annotations'},
    'function': {'namespaces', 'arguments', 'returns', 'package'}
}

VALID_OBJECTS = set(VALID_INFORMATION.keys())


def _is_static_method(function):
    # Checks if the function object is decorated with `staticmethod`
    if type(function).__qualname__ == "method_descriptor":
        # Ignore method descriptors
        return False
    name = function.__qualname__.rsplit('.', 1)[-1]
    cls = inspect._findclass(function)
    if cls is not None:
        method = inspect.getattr_static(cls, name)
        return isinstance(method, staticmethod)
    return False


def update_ontology_information(obj, obj_type, obj_iri, namespaces=None,
                                **kwargs):
    """
    Updates the ontology information in a Python object. This can be a
    function or an object holding data.

    Parameters
    ----------
    obj : object
        Function or data object. It must allow attribute assignment.
    obj_type : {'function', 'data_object'}
        Defines the type of object being annotated. This is also used to filter
        additional information that can be annotated using `kwargs`.
    obj_iri : str
        IRI of the class representing `obj`.
    namespaces : dict, optional
        Dictionary where the keys are the prefixes of the namespaces used in
        the annotations, and the values are the IRI representing the namespace.
        If None, no namespace is used.
        Default: None
    kwargs : dict, optional
        Additional information on the object `obj`. The key is the type of
        information, and the values are a dictionary, where the keys identify
        the elements to be annotated and the values are the IRIs of the
        ontology identifying the element. The valid types of information
        depend on `obj_type`:
        * `obj_type='function'`: `arguments` (identify the names of any argument
          present in the function definition) or `returns` (annotate one
          or more returns). In case of tuple returns, the key in the
          dictionary is an integer with the order of the object returned.
        * `obj_type='data_object'`: `attributes` (identify the names of object
          attributes) or `annotations` (identify the names of annotations).
          Annotations are special values stored in a dictionary that can be
          acessed by an object attribute.
    """
    if obj_type not in VALID_OBJECTS:
        raise ValueError(f"Invalid object type: {obj_type}")

    obj.__ontology__ = {obj_type: obj_iri}

    if namespaces is not None:
        kwargs['namespaces'] = namespaces

    valid_info = VALID_INFORMATION[obj_type]
    for information_type, value in kwargs.items():
        if information_type in valid_info:
            if value:
                obj.__ontology__[information_type] = deepcopy(value)
        else:
            raise ValueError(f"Invalid information type for {obj_type}: "
                             f"{information_type}. Valid information are: "
                             f"{', '.join(valid_info)}")

    return obj


def annotate_function(function_iri, **kwargs):

    def wrapped(function):
        is_static = _is_static_method(function)
        annotated = update_ontology_information(function, obj_type='function',
                                                obj_iri=function_iri, **kwargs)

        # If the function is decorated with `staticmethod`, restore the
        # decorator (otherwise `self` will be passed as first argument when
        # calling the function)
        return staticmethod(annotated) if is_static else annotated

    return wrapped


def annotate_object(object_iri, **kwargs):

    def wrapped(cls):
        return update_ontology_information(cls, obj_type='data_object',
                                           obj_iri=object_iri, **kwargs)

    return wrapped


annotate_neao = partial(annotate_function,
                        namespaces={"neao_base": "http://purl.org/neao/base#",
                                    "neao_data": "http://purl.org/neao/data#",
                                    "neao_steps": "http://purl.org/neao/steps#",
                                    "neao_params": "http://purl.org/neao/params#"})
