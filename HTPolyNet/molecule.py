from itertools import combinations_with_replacement, product
from copy import deepcopy
import pandas as pd
import logging

class ReactiveAtom:
    def __init__(self,datadict,name=''):
        self.name=name
        # z: maximum number of bonds this atom will form
        # in a crosslinking reaction
        self.z=int(datadict.get("z",1))
        # ht: a Head or Tail designation; Heads can only 
        # react with Tails, and vice versa, if specified
        self.ht=datadict.get("ht",None)
        # sym: list of other reactive atoms in the
        # owning monomer that are in the same symmetry class
        # THIS MUST BE USER-SPECIFIED 
        self.sym=datadict.get("sym",[])
    def __str__(self):
        return f'{self.name}: ({self.z})({self.ht})({self.sym})'
    def to_yaml(self):
        return r'{'+f'z: {self.z}, ht: {self.ht}, sym: {self.sym}'+r'}'

class CappingBond:
    boc={1:'-',2:'=',3:'≡'}
    def __init__(self,jsondict):
        self.pairnames=jsondict["pair"]
        self.bondorder=jsondict.get("order",1)
        self.deletes=jsondict.get("deletes",[])
    def to_yaml(self):
        return r'{'+f'pair: {self.pairnames}, order: {self.bondorder}, deletes: {self.deletes}'+r'}'
    def __str__(self):
        s=self.pairnames[0]+CappingBond.boc[self.bondorder]+self.pairnames[1]
        if len(self.deletes)>0:
            s+=' D['+','.join(self.deletes)+']'
        return s

class Oligomer:
    def __init__(self,top=None,coord=None,stoich=[]):
        self.topology=top
        self.coord=coord
        self.stoich=stoich
        self.unlinked_topology=None
    
    def analyze(self):
        # this is not really used
        logging.info('Oligomer.analyze begins.')
        L=self.topology
        U=self.unlinked_topology
        for typ in ['atomtypes','bondtypes','angletypes','dihedraltypes']:
            l=L.D[typ]
            u=U.D[typ]
            mdf=pd.concat((l,u),ignore_index=True)
            # logging.info(f'L:\n'+l.to_string())
            # logging.info(f'u:\n'+u.to_string())
            # logging.info(f'mdf:\n'+mdf.to_string())
            dups=mdf.duplicated(keep=False)
            xsec=mdf[dups]
            sd=mdf[~dups]
            # logging.info(f'sd:\n'+sd.to_string())
            smdf=pd.concat((l,xsec),ignore_index=True)
            dups=smdf.duplicated(keep=False)
            l_not_u=xsec[~dups]
        #     logging.info(f'l!u:\n'+l_not_u.to_string())

        #     logging.info(f'Oligomer.analyze: L.D[{typ}].shape {l.shape} U.D[{typ}].shape {u.shape}')
            logging.info(f'{typ}: in oligomer top but not in union of monomer tops: {l_not_u.shape[0]}')
        # logging.info('Oligomer.analyze ends.')

class Monomer:
    def __init__(self,jsondict,name=''):
        self.name=jsondict.get("name",name)
        self.Topology={}
        self.Topology["active"]=None
        self.Coords={}
        self.Coords["active"]=None
        self.reactive_atoms={name:ReactiveAtom(data,name=name) for name,data in jsondict["reactive_atoms"].items()}
        if "capping_bonds" in jsondict:
            self.capping_bonds=[CappingBond(data) for data in jsondict["capping_bonds"]]
            self.Topology["inactive"]=None
            self.Coords["inactive"]=None
        else:
            self.capping_bonds=[]

    def update_atom_specs(self,newmol2,oldmol2):
        ''' Atom specifications from the configuration file refer to atom names in the
            user-provided mol2 files.  After processing via ambertools, the output mol2
            files have renamed atoms (potentially) in the same order as the atoms in the
            user-provided mol3.  This method updates the user-provided atom specifications
            so that they reflect the atom names generated by ambertools. '''
        oa=oldmol2.D['atoms']
        na=newmol2.D['atoms']
        for n,d in self.reactive_atoms.items():
            idx=oa[oa['atomName']==n]['globalIdx'].values[0]
            nn=na[na['globalIdx']==idx]['atomName'].values[0]
            t=d
            self.reactive_atoms[n]=None
            self.reactive_atoms[nn]=t
        for c in self.capping_bonds:
            p=c.pairnames
            newpairnames=[]
            for n in p:
                idx=oa[oa['atomName']==n]['globalIdx'].values[0]
                nn=na[na['globalIdx']==idx]['atomName'].values[0]
                newpairnames.append(nn)
            c.pairnames=newpairnames

    def __str__(self):
        s=self.name+'\n'
        for r,a in self.reactive_atoms.items():
            s+=f'   reactive atom: {r}:'+str(a)+'\n'
        for c in self.capping_bonds:
            s+='   cap: '+str(c)+'\n'
        return s

class Reaction:
    def __init__(self,jsondict):
        self.reactants=jsondict.get("reactants",[])
        self.probability=jsondict.get("probability",1.0)
    def __str__(self):
        return 'Reaction: '+'+'.join(self.reactants)+' : '+str(self.probability)

def get_conn(mol):
    conn=[]
    for mrname,mr in mol.reactive_atoms.items():
        ''' check to see if this atom's symmetry partners are already on the list '''
        donotadd=False
        for s in mr.sym:
            if s in conn:
                donotadd=True
        if not donotadd:
            conn.append(mrname)
    return conn

def oligomerize(m,n):
    ''' m and n are Monomer instances (defined in here) '''
    if not isinstance(m,Monomer) or not isinstance(n,Monomer):
        raise Exception(f'react_mol2 needs Monomers not {type(m)} and {type(n)}')
    if not 'active' in m.Topology or not 'active' in n.Topology:
        raise Exception('react_mol2 needs Monomers with active topologies')
    if not 'active' in m.Coords or not 'active' in n.Coords:
        raise Exception('react_mol2 needs Monomers with active coordinates')
    oligdict={}
    # print(f'react_mol2: {m.name} and {n.name}')
    for basemol,othermol in zip([m,n],[n,m]):
        # list of all asymmetric reactive atoms on base
        basera=get_conn(basemol)
        # number of connections for each of those reactive atoms
        baseconn=[basemol.reactive_atoms[i].z for i in basera]
        # list of all asymmetric reactive atoms on other
        otherra=get_conn(othermol)
        # options for a connection on basemol are empty ('') or any one of 
        # asymmetric atoms on other
        otherra=['']+otherra
        # enumerate all symmetry-unique configurations of oligomers
        # on *each* reactive atom on basemol *independently*, for all
        # connections on each reactive atom
        basearr=[]
        for z in baseconn:
            # this reactive atom has z connections, each of which can be
            # 'occupied' by one member of otherra in all possible combinations
            basearr.append(list(combinations_with_replacement(otherra,z)))
        # for n,c in zip(basera,basearr):
        #     print(f'{n} can have following connection configurations:',c)
        # enumerate all unique configurations of connections on all reactive
        # atoms.  This is relevant if there is more than one asymmetric 
        # reactive atom on basemol.
        o=product(*basearr)
        # the first one is one where all connections on all reactive atoms
        # of basemol are empty, so skip it
        next(o)
        for oligo in o:
            # logging.debug('making oligo',oligo)
            # make working copy of basemol coordinates
            wc=deepcopy(basemol.Coords['active'])
            stoich=[(basemol,1)]
            oname=basemol.name
            for c,b in zip(oligo,basera):
                # print(f'establishing connection(s) to atom {b} of {basemol.name}:')
                nconn=len([x for x in c if x!=''])
                if nconn>0:
                    oname+=f'@{b}-'+','.join([f'{othermol.name}#{a}' for a in c if a!=''])
                oc=0
                for a in c:
                    # print(f'  to atom {a} of {othermol.name}')
                    if a != '':
                        owc=deepcopy(othermol.Coords['active'])
                        oc+=1
                        # bring copy of coords from othermol into 
                        # working copy of basemol
                        wc.bond_to(owc,acc=b,don=a)
                if oc>0:
                    stoich.append((othermol,oc))
            # print('-> prefix',oname)
            # wc.write_mol2(f'OLIG-{oname}.mol2')
            oligdict[oname]=Oligomer(coord=wc,stoich=stoich)

    return oligdict