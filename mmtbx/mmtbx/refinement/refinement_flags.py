from copy import deepcopy
from cctbx.array_family import flex
import sys, os, math, string
from libtbx.test_utils import approx_equal
from libtbx import adopt_init_args
from libtbx.utils import Sorry

class manager(object):
  def __init__(self, individual_sites       = False,
                     rigid_body             = False,
                     individual_adp         = False,
                     group_adp              = False,
                     tls                    = False,
                     individual_occupancies = False,
                     group_occupancies      = False,
                     group_anomalous        = False,
                     sites_individual       = None,
                     sites_rigid_body       = None,
                     adp_individual_iso     = None,
                     adp_individual_aniso   = None,
                     adp_group              = None,
                     group_h                = None,
                     adp_tls                = None,
                     occupancies_individual = None,
                     occupancies_group      = None):
                     # XXX group_anomalous should be here
    adopt_init_args(self, locals())
    self.check_all()

  def _deep_copy(self, x):
    result = []
    if(x is None): result = x
    elif(self.is_bool(x) or self.is_size_t(x)):
      result = x.deep_copy()
    else:
      for item in x:
        if(self.is_bool(item) or self.is_size_t(item)):
          result.append(item.deep_copy())
        else: result.append(item[:])
    return result

  def deep_copy(self):
    return manager(
      individual_sites       = self.individual_sites,
      rigid_body             = self.rigid_body,
      individual_adp         = self.individual_adp,
      group_adp              = self.group_adp,
      tls                    = self.tls,
      individual_occupancies = self.individual_occupancies,
      group_occupancies      = self.group_occupancies,
      group_anomalous        = self.group_anomalous,
      sites_individual       = self._deep_copy(self.sites_individual),
      sites_rigid_body       = self._deep_copy(self.sites_rigid_body),
      adp_individual_iso     = self._deep_copy(self.adp_individual_iso),
      adp_individual_aniso   = self._deep_copy(self.adp_individual_aniso),
      adp_group              = self._deep_copy(self.adp_group),
      group_h                = self._deep_copy(self.group_h),
      adp_tls                = self._deep_copy(self.adp_tls),
      occupancies_individual = self._deep_copy(self.occupancies_individual),
      occupancies_group      = self._deep_copy(self.occupancies_group))
      # XXX group_anomalous should be here

  def is_size_t(self, x):
    return ("%s"%x.__class__).count("array_family_flex_ext.size_t") > 0

  def is_bool(self, x):
    return ("%s"%x.__class__).count("array_family_flex_ext.bool") > 0

  def _count_selected(self, selections):
    assert selections is not None
    selections = self._deep_copy(selections)
    result = True
    try: lx = len(selections)
    except: lx = selections.size()
    if(lx == 0): return result
    if(self.is_bool(selections)):
      if(selections.count(True) == 0): result = False
    elif(self.is_size_t(selections)):
      if(selections.size() == 0): result = False
    else:
      for sel in selections:
        if(self.is_size_t(sel)):
          if(sel.size() == 0):
            result = False
            break
        elif(self.is_bool(sel)):
          if(sel.count(True) == 0):
            result = False
            break
        elif(len(sel) == 0):
          result = False
          break
      sel0 = selections[0]
      if(self.is_bool(sel0)):
        for sel in selections[1:]:
          if(not self.is_bool(sel)):
            result = False
          sel0 &= sel
        if(not sel0.all_eq(False)):
          result = False
      else:
        if(not self.is_size_t(sel0)): sel0 = flex.size_t(sel0)
        for sel in selections[1:]:
          if(not self.is_size_t(sel)): sel = flex.size_t(sel)
          sel0.extend(sel)
        perm = flex.sort_permutation(sel0)
        sel0_ = sel0.select(perm)
        sz = sel0_.size()
        for i,e in enumerate(sel0_):
          if(i+1 < sz):
            if(sel0_[i]-sel0_[i+1]==0):
              result = False
              break
    return result

  def check_all(self):
    prefix = "\nBad (empty or mixed) selection in %s"
    if(self.individual_sites):
      if(not self._count_selected(self.sites_individual)):
        raise Sorry(prefix%"sites_individual.")
    if(self.rigid_body):
      if(not self._count_selected(self.sites_rigid_body)):
        raise Sorry(prefix%"sites_rigid_body.")
    if(self.individual_adp):
      if(not self.tls and [self.adp_individual_iso,
         self.adp_individual_aniso].count(None)==0):
        if(not (self.adp_individual_aniso &
           self.adp_individual_iso).all_eq(False)):
          raise Sorry("Same atoms selected for iso and aniso ADP refinement.")
      elif(self.adp_individual_iso is not None):
        if(not self._count_selected(self.adp_individual_iso)):
          raise Sorry(prefix%"adp_individual_iso.")
      elif(self.adp_individual_aniso is not None):
        if(not self._count_selected(self.adp_individual_aniso)):
          raise Sorry(prefix%"adp_individual_aniso.")
      else: raise Sorry("No selection for individual_adp.")
    if(self.group_adp):
      if(not self._count_selected(self.adp_group)):
        raise Sorry(prefix%"adp_group.")
    if(self.tls):
      if(not self._count_selected(self.adp_tls)):
        raise Sorry(prefix%"adp_tls.")
    if(self.individual_occupancies):
      if(not self._count_selected(self.occupancies_individual)):
        raise Sorry(prefix%"occupancies_individual.")
    if(self.group_occupancies):
      if(not self._count_selected(self.occupancies_group)):
        raise Sorry(prefix%"occupancies_group.")
    if(self.group_anomalous):
      pass # XXX selections not used in common framework

  def szs(self, x):
    if(x is not None): return str(len(x))
    else: return str(0)

  def ca(self, x):
    if(x is None):           return str(0)
    elif(self.is_bool(x)):   return str(x.count(True))
    elif(self.is_size_t(x)): return str(x.size())
    elif(len(x)==0):         return str(0)
    elif(self.is_bool(x[0])):
      return str(flex.sum(flex.size_t([i.count(True) for i in x])))
    elif(self.is_size_t(x[0])):
      return str(flex.sum(flex.size_t([i.size() for i in x])))
    else:
      cntr = 0
      for i in x:
        for ii in i:
          cntr += 1
      return str(cntr)

  def show(self, log = None):
    if(log is None): log = sys.stdout
    print >> log, "Refinement flags and selection counts:"
    print >> log, "  individual_sites       = %5s (%s atoms)"%(
      str(self.individual_sites), self.ca(self.sites_individual))
    print >> log, "  rigid_body             = %5s (%s atoms in %s groups)"%(
      str(self.rigid_body), self.ca(self.sites_rigid_body),
      self.szs(self.sites_rigid_body))
    print >> log, "  individual_adp         = %5s (iso = %s aniso = %s)"%(
      str(self.individual_adp), self.ca(self.adp_individual_iso),
      self.ca(self.adp_individual_aniso))
    print >> log, "  group_adp              = %5s (%s atoms in %s groups)"%(
      str(self.group_adp), self.ca(self.adp_group), self.szs(self.adp_group))
    print >> log, "  tls                    = %5s (%s atoms in %s groups)" % (
      str(self.tls), self.ca(self.adp_tls), self.szs(self.adp_tls))
    print >> log, "  individual_occupancies = %5s (%s atoms)"%(
      str(self.individual_occupancies), self.ca(self.occupancies_individual))
    print >> log, "  group_occupancies      = %5s (%s atoms in %s groups)"%(
     str(self.group_occupancies), self.ca(self.occupancies_group),
     self.szs(self.occupancies_group))
    print >> log, "  group_anomalous        = %5s"%self.group_anomalous # XXX selections not available

  def _select(self, x, selection):
    try: lx = len(x)
    except: lx = x.size()
    if(lx == 0): return x
    if(self.is_bool(x)):
      x = x.select(selection)
    elif(self.is_bool(x[0])):
      x_new = []
      for i_seq, item in enumerate(x):
        val = item.select(selection)
        if(val.count(True) > 0): x_new.append(val)
      x = x_new
    elif(self.is_size_t(x[0])):
      x_new = []
      for i_seq, item in enumerate(x):
        val = flex.bool(selection.size(), item).select(selection).iselection()
        if(val.size() > 0): x_new.append(val)
      x = x_new
    else:
      assert ("%s"%x.__class__).count("list") or \
             ("%s"%x.__class__).count("tuple")
      result = []
      for x_ in x:
        result_ = list(flex.bool(selection.size(),
          flex.size_t(x_)).select(selection).iselection())
        if(len(result_)>0):
          result.append(result_)
      x = result
    return x

  def select(self, selection):
    assert self.is_bool(selection)
    if(self.sites_individual is not None):
      self.sites_individual = self._select(self.sites_individual, selection)
    if(self.adp_individual_iso is not None):
      self.adp_individual_iso= self._select(self.adp_individual_iso, selection)
    if(self.adp_individual_aniso is not None):
      self.adp_individual_aniso= self._select(self.adp_individual_aniso,
        selection)
    if(self.sites_rigid_body is not None):
      self.sites_rigid_body = self._select(self.sites_rigid_body, selection)
    if(self.adp_group is not None):
      self.adp_group = self._select(self.adp_group, selection)
    if(self.group_h is not None):
      self.group_h = self._select(self.group_h, selection)
    if(self.adp_tls is not None):
      self.adp_tls = self._select(self.adp_tls, selection)
    if(self.occupancies_individual is not None):
      self.occupancies_individual = self._select(self.occupancies_individual,
        selection)
    if(self.occupancies_group is not None):
      self.occupancies_group = self._select(self.occupancies_group, selection)
    # XXX group_anomalous selection should be added
    return self

  def inflate(self, sites_individual       = None,
                    sites_rigid_body       = None,
                    adp_individual_iso     = None,
                    adp_individual_aniso   = None,
                    adp_group              = None,
                    group_h                = None,
                    adp_tls                = None,
                    occupancies_individual = None,
                    occupancies_group      = None):
    if(sites_individual is not None):
      assert self.is_bool(sites_individual)
      self.sites_individual.extend(sites_individual)
    if(adp_individual_iso is not None):
      assert self.is_bool(adp_individual_iso)
      self.adp_individual_iso.extend(adp_individual_iso)
    if(adp_individual_aniso is not None):
      assert self.is_bool(adp_individual_aniso)
      self.adp_individual_aniso.extend(adp_individual_aniso)
    if(sites_rigid_body is not None):
      assert hasattr(sites_rigid_body, 'count')
      self.sites_rigid_body.append(sites_rigid_body)
    if(adp_group is not None):
      assert hasattr(adp_group, 'count')
      self.adp_group.append(adp_group)
    if(group_h is not None):
      assert hasattr(group_h, 'count')
      self.group_h.append(group_h)
    if(adp_tls is not None):
      assert hasattr(adp_tls, 'count')
      self.adp_tls.append(adp_tls)
    if(occupancies_individual is not None):
      assert hasattr(occupancies_individual, 'count')
      self.occupancies_individual.extend(occupancies_individual)
    if(occupancies_group is not None):
      assert hasattr(occupancies_group, 'count')
      self.occupancies_group.append(occupancies_group)
    self.check_all()
    return self
