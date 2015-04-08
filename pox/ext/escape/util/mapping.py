# Copyright 2015 Janos Czentye
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Contains abstract classes for NFFG mapping

:class:`AbstractMapper` is an abstract class for orchestration method which
should implement mapping preparations and invoke actual mapping algorithm

:class:`AbstractMappingStrategy` is an abstract class for containing entirely
the mapping algorithm as a class method
"""
import importlib
import threading

from escape import CONFIG
from escape.service import LAYER_NAME as SAS
from escape.orchest import LAYER_NAME as ROS

from escape.util.misc import call_as_coop_task
from pox.lib.revent.revent import EventMixin
from pox import core


class AbstractMappingStrategy(object):
  """
  Abstract class for the mapping strategies

  Follows the Strategy design pattern
  """

  def __init__ (self):
    """
    Init
    """
    super(AbstractMappingStrategy, self).__init__()

  @classmethod
  def map (cls, graph, resource):
    """
    Abstract function for mapping algorithm

    :param graph: Input graph which need to be mapped
    :type graph: NFFG
    :param resource: resource info
    :type resource: NFFG
    :raise: NotImplementedError
    :return: mapped graph
    :rtype: NFFG
    """
    raise NotImplementedError("Derived class must override this function!")


class AbstractMapper(EventMixin):
  """
  Abstract class for graph mapping function

  Inherited from :class`EventMixin` to implement internal event-based
  communication

  Contain common functions and initialization
  """
  __defaults = {SAS: 'DefaultServiceMappingStrategy',
                ROS: 'ESCAPEMappingStrategy'}

  def __init__ (self, layer_name, strategy=None, threaded=None):
    """
    Init
    """
    # Set threaded
    if threaded is not None:
      self._threaded = threaded
    elif 'THREADED' in CONFIG[layer_name]:
      self._threaded = CONFIG[layer_name]['THREADED']
    else:
      self._threaded = False
    # Set strategy
    if strategy is not None:
      if issubclass(strategy, AbstractMappingStrategy):
        self.strategy = strategy
      else:
        raise AttributeError(
          "Mapping strategy is not subclass of AbstractMappingStrategy!")
    elif 'STRATEGY' in CONFIG[layer_name]:
      if layer_name == SAS:
        strategy_class = getattr(
          importlib.import_module("escape.service.sas_mapping"),
          CONFIG[layer_name]['STRATEGY'])
      elif layer_name == ROS:
        strategy_class = getattr(
          importlib.import_module("escape.orchest.ros_mapping"),
          CONFIG[layer_name]['STRATEGY'])
      else:
        raise AttributeError(
          "Layer name: %s is not defined in CONFIG" % layer_name)
      if issubclass(strategy_class, AbstractMappingStrategy):
        self.strategy = strategy_class
      else:
        raise AttributeError(
          "Mapping strategy is not subclass of AbstractMappingStrategy!")
    else:
      self.strategy = self.__defaults[layer_name]
    super(AbstractMapper, self).__init__()

  def orchestrate (self, input_graph, resource_view):
    """
    Abstract function for wrapping optional steps connected to orchestration

    Implemented function call the mapping algorithm

    :param input_graph: graph representation which need to be mapped
    :type input_graph: NFFG
    :param resource_view: resource information
    :type resource_view: AbstractVirtualizer
    :raise: NotImplementedError
    :return: mapped graph
    :rtype: NFFG
    """
    raise NotImplementedError("Derived class must override this function!")

  def _start_mapping (self, graph, resource):
    """
    Run mapping algorithm in a separate Python thread

    :param graph: Network Function Forwarding Graph
    :type graph: NFFG
    :param resource: global resource
    :type resource: NFFG
    :return: None
    """

    def run ():
      core.getLogger("worker").info(
        "Schedule mapping algorithm: %s" % self.strategy.__name__)
      nffg = self.strategy.map(graph=graph, resource=resource)
      # Must use call_as_coop_task because we want to call a function in a
      # coop microtask environment from a separate thread
      call_as_coop_task(self._mapping_finished, nffg=nffg)

    core.getLogger("worker").debug("Initialize working thread...")
    self._mapping_thread = threading.Thread(target=run)
    self._mapping_thread.daemon = True
    self._mapping_thread.start()

  def _mapping_finished (self, nffg):
    """
    Called from a separate thread when the mapping process is finished

    :param nffg: geenrated NF-FG
    :type nffg: NFFG
    :return: None
    """
    raise NotImplementedError("Derived class must override this function!")