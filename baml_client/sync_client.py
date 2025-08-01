###############################################################################
#
#  Welcome to Baml! To use this generated code, please run the following:
#
#  $ pip install baml-py
#
###############################################################################

# This file was generated by BAML: please do not edit it. Instead, edit the
# BAML files and re-generate this code.
#
# ruff: noqa: E501,F401
# flake8: noqa: E501,F401
# pylint: disable=unused-import,line-too-long
# fmt: off
from typing import Dict, List, Optional, TypeVar, Union, cast
from typing_extensions import Literal

import baml_py

from . import _baml
from ._baml import BamlCallOptions
from .types import Checked, Check
from .parser import LlmResponseParser, LlmStreamParser
from .sync_request import HttpRequest, HttpStreamRequest
from .globals import DO_NOT_USE_DIRECTLY_UNLESS_YOU_KNOW_WHAT_YOURE_DOING_CTX, DO_NOT_USE_DIRECTLY_UNLESS_YOU_KNOW_WHAT_YOURE_DOING_RUNTIME


OutputType = TypeVar('OutputType')


class BamlSyncClient:
    __runtime: baml_py.BamlRuntime
    __ctx_manager: baml_py.BamlCtxManager
    __stream_client: "BamlStreamClient"
    __http_request: HttpRequest
    __http_stream_request: HttpStreamRequest
    __llm_response_parser: LlmResponseParser
    __llm_stream_parser: LlmStreamParser
    __baml_options: _baml.BamlCallOptions

    def __init__(self, runtime: baml_py.BamlRuntime, ctx_manager: baml_py.BamlCtxManager, baml_options: Optional[_baml.BamlCallOptions] = None):
      self.__runtime = runtime
      self.__ctx_manager = ctx_manager
      self.__stream_client = BamlStreamClient(self.__runtime, self.__ctx_manager, baml_options)
      self.__http_request = HttpRequest(self.__runtime, self.__ctx_manager)
      self.__http_stream_request = HttpStreamRequest(self.__runtime, self.__ctx_manager)
      self.__llm_response_parser = LlmResponseParser(self.__runtime, self.__ctx_manager)
      self.__llm_stream_parser = LlmStreamParser(self.__runtime, self.__ctx_manager)
      self.__baml_options = baml_options or {}

    @property
    def stream(self):
      return self.__stream_client

    @property
    def request(self):
      return self.__http_request

    @property
    def stream_request(self):
      return self.__http_stream_request

    @property
    def parse(self):
      return self.__llm_response_parser

    @property
    def parse_stream(self):
      return self.__llm_stream_parser

    def with_options(
      self,
      tb: Optional[_baml.type_builder.TypeBuilder] = None,
      client_registry: Optional[baml_py.baml_py.ClientRegistry] = None,
      collector: Optional[Union[baml_py.baml_py.Collector, List[baml_py.baml_py.Collector]]] = None,
      env: Optional[Dict[str, str]] = None,
    ) -> "BamlSyncClient":
      """
      Returns a new instance of BamlSyncClient with explicitly typed baml options
      for Python 3.8 compatibility.
      """
      new_options: _baml.BamlCallOptions = self.__baml_options.copy()

      # Override if any keyword arguments were provided.
      if tb is not None:
          new_options["tb"] = tb
      if client_registry is not None:
          new_options["client_registry"] = client_registry
      if collector is not None:
          new_options["collector"] = collector
      if env is not None:
          new_options["env"] = env
      return BamlSyncClient(self.__runtime, self.__ctx_manager, new_options)

    
    def ExtractResume(
        self,
        resume: str,
        baml_options: _baml.BamlCallOptions = {},
    ) -> _baml.types.Resume:
      options: _baml.BamlCallOptions = {**self.__baml_options, **(baml_options or {})}
      __tb__ = options.get("tb", None)
      if __tb__ is not None:
        tb = __tb__._tb # type: ignore (we know how to use this private attribute)
      else:
        tb = None
      __cr__ = options.get("client_registry", None)
      collector = options.get("collector", None)
      collectors = collector if isinstance(collector, list) else [collector] if collector is not None else []
      env = _baml.env_vars_to_dict(options.get("env", {}))
      raw = self.__runtime.call_function_sync(
        "ExtractResume",
        {
          "resume": resume,
        },
        self.__ctx_manager.get(),
        tb,
        __cr__,
        collectors,
        env,
      )
      return cast(_baml.types.Resume, raw.cast_to(_baml.types, _baml.types, _baml.partial_types, False))
    



class BamlStreamClient:
    __runtime: baml_py.BamlRuntime
    __ctx_manager: baml_py.BamlCtxManager
    __baml_options: _baml.BamlCallOptions
    def __init__(self, runtime: baml_py.BamlRuntime, ctx_manager: baml_py.BamlCtxManager, baml_options: Optional[_baml.BamlCallOptions] = None):
      self.__runtime = runtime
      self.__ctx_manager = ctx_manager
      self.__baml_options = baml_options or {}

    
    def ExtractResume(
        self,
        resume: str,
        baml_options: _baml.BamlCallOptions = {},
    ) -> baml_py.BamlSyncStream[_baml.partial_types.Resume, _baml.types.Resume]:
      options: _baml.BamlCallOptions = {**self.__baml_options, **(baml_options or {})}
      __tb__ = options.get("tb", None)
      if __tb__ is not None:
        tb = __tb__._tb # type: ignore (we know how to use this private attribute)
      else:
        tb = None
      __cr__ = options.get("client_registry", None)
      collector = options.get("collector", None)
      collectors = collector if isinstance(collector, list) else [collector] if collector is not None else []
      env = _baml.env_vars_to_dict(options.get("env", {}))
      raw = self.__runtime.stream_function_sync(
        "ExtractResume",
        {
          "resume": resume,
        },
        None,
        self.__ctx_manager.get(),
        tb,
        __cr__,
        collectors,
        env,
      )

      return baml_py.BamlSyncStream[_baml.partial_types.Resume, _baml.types.Resume](
        raw,
        lambda x: cast(_baml.partial_types.Resume, x.cast_to(_baml.types, _baml.types, _baml.partial_types, True)),
        lambda x: cast(_baml.types.Resume, x.cast_to(_baml.types, _baml.types, _baml.partial_types, False)),
        self.__ctx_manager.get(),
      )
    


b = BamlSyncClient(DO_NOT_USE_DIRECTLY_UNLESS_YOU_KNOW_WHAT_YOURE_DOING_RUNTIME, DO_NOT_USE_DIRECTLY_UNLESS_YOU_KNOW_WHAT_YOURE_DOING_CTX)

__all__ = ["b", "BamlCallOptions"]