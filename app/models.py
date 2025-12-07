"""
SQLAlchemy Database Models
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Drug(db.Model):
    """Drug model"""
    __tablename__ = 'drugs'
    
    cid = db.Column(db.String, primary_key=True)
    drug_name = db.Column(db.String, nullable=False, index=True)
    drugbank_id = db.Column(db.String, index=True)
    synonyms = db.Column(db.Text)
    cas = db.Column(db.String)
    unii = db.Column(db.String)
    inchi_key = db.Column(db.String)
    
    # Relationships
    atc_codes = db.relationship('ATCCode', backref='drug', lazy='dynamic')
    side_effects = db.relationship('DrugSideEffect', backref='drug', lazy='dynamic')
    
    def to_dict(self):
        return {
            'cid': self.cid,
            'drug_name': self.drug_name,
            'drugbank_id': self.drugbank_id
        }

class ATCCode(db.Model):
    """ATC Code model"""
    __tablename__ = 'atc_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    cid = db.Column(db.String, db.ForeignKey('drugs.cid'), nullable=False, index=True)
    atc_code = db.Column(db.String, nullable=False, index=True)
    atc_level1 = db.Column(db.String)
    atc_level2 = db.Column(db.String)
    atc_level3 = db.Column(db.String)
    atc_level4 = db.Column(db.String)
    atc_level5 = db.Column(db.String)

class SideEffect(db.Model):
    """Side Effect model"""
    __tablename__ = 'side_effects'
    
    id = db.Column(db.Integer, primary_key=True)
    meddra_code = db.Column(db.String, unique=True, nullable=False)
    side_effect_name = db.Column(db.String, nullable=False, index=True)
    term_type = db.Column(db.String)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.side_effect_name,
            'code': self.meddra_code
        }

class DrugSideEffect(db.Model):
    """Drug-Side Effect mapping"""
    __tablename__ = 'drug_side_effects'
    
    id = db.Column(db.Integer, primary_key=True)
    cid = db.Column(db.String, db.ForeignKey('drugs.cid'), nullable=False, index=True)
    side_effect_id = db.Column(db.Integer, db.ForeignKey('side_effects.id'), nullable=False)
    
    # Relationship to side effect
    side_effect = db.relationship('SideEffect', backref='drug_mappings')
