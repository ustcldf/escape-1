# Copyright 2015 Janos Czentye <czentye@tmit.bme.hu>
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
Contains classes relevant to Resource Orchestration Sublayer functionality.
"""
from escape.orchest.ros_mapping import ResourceOrchestrationMapper
from escape.orchest import log as log, LAYER_NAME
from escape.orchest.virtualization_mgmt import AbstractVirtualizer, \
  VirtualizerManager
from escape.util.mapping import AbstractOrchestrator


class ResourceOrchestrator(AbstractOrchestrator):
  """
  Main class for the handling of the ROS-level mapping functions.
  """
  # Default Mapper class as a fallback mapper
  DEFAULT_MAPPER = ResourceOrchestrationMapper

  def __init__ (self, layer_API):
    """
    Initialize main Resource Orchestration Layer components.

    :param layer_API: layer API instance
    :type layer_API: :any:`ResourceOrchestrationAPI`
    :return: None
    """
    super(ResourceOrchestrator, self).__init__(LAYER_NAME)
    log.debug("Init %s" % self.__class__.__name__)
    self.nffgManager = NFFGManager()
    # Init virtualizer manager
    # Listeners must be weak references in order the layer API can garbage
    # collected
    self.virtualizerManager = VirtualizerManager()
    self.virtualizerManager.addListeners(layer_API, weak=True)
    # Init RO Mapper listeners
    # Listeners must be weak references in order the layer API can garbage
    # collected
    # self.mapper is set by the AbstractOrchestrator's constructor
    self.mapper.addListeners(layer_API, weak=True)
    # Init NFIB manager
    self.nfibManager = NFIBManager()

  def instantiate_nffg (self, nffg):
    """
    Main API function for NF-FG instantiation.

    :param nffg: NFFG instance
    :type nffg: :any:`NFFG`
    :return: mapped NFFG instance
    :rtype: :any:`NFFG`
    """
    log.debug("Invoke %s to instantiate NF-FG" % self.__class__.__name__)
    # Store newly created NF-FG
    self.nffgManager.save(nffg)
    # Get Domain Virtualizer to acquire global domain view
    global_view = self.virtualizerManager.dov
    if global_view is not None:
      if isinstance(global_view, AbstractVirtualizer):
        # Run Nf-FG mapping orchestration
        mapped_nffg = self.mapper.orchestrate(nffg, global_view)
        log.debug(
          "NF-FG instantiation is finished by %s" % self.__class__.__name__)
        return mapped_nffg
      else:
        log.warning("Global view is not subclass of AbstractVirtualizer!")
    else:
      log.warning("Global view is not acquired correctly!")
    log.error("Abort mapping process!")


class NFFGManager(object):
  """
  Store, handle and organize Network Function Forwarding Graphs.
  """

  def __init__ (self):
    """
    Init.
    """
    super(NFFGManager, self).__init__()
    log.debug("Init %s" % self.__class__.__name__)
    self._nffgs = dict()

  def save (self, nffg):
    """
    Save NF-FG in a dict.

    :param nffg: Network Function Forwarding Graph
    :type nffg: :any:`NFFG`
    :return: generated ID of given NF-FG
    :rtype: int
    """
    nffg_id = self._generate_id(nffg)
    self._nffgs[nffg_id] = nffg
    log.debug("NF-FG: %s is saved by %s with id: %s" % (
      nffg, self.__class__.__name__, nffg_id))
    return nffg.id

  def _generate_id (self, nffg):
    """
    Try to generate a unique id for NFFG.

    :param nffg: NFFG
    :type nffg: :nay:`NFFG`
    """
    tmp = nffg.id if nffg.id is not None else id(nffg)
    if tmp in self._nffgs:
      tmp = len(self._nffgs)
      if tmp in self._nffgs:
        for i in xrange(100):
          tmp += i
          if tmp not in self._nffgs:
            return tmp
        else:
          raise RuntimeError("Can't be able to generate a unique id!")
    return tmp

  def get (self, nffg_id):
    """
    Return NF-FG with given id.

    :param nffg_id: ID of NF-FG
    :type nffg_id: int
    :return: NF-Fg instance
    :rtype: :any:`NFFG`
    """
    return self._nffgs.get(nffg_id, default=None)


class NFIBManager(object):
  """
  Manage the handling of Network Function Information Base.
  """

  def __init__ (self):
    """
    Init.
    """
    super(NFIBManager, self).__init__()

  def add (self, nf):
    # TODO - implement
    pass

  def remove (self, nf_id):
    # TODO - implement
    pass

  def getNF (self, nf_id):
    # TODO - implement
    pass
