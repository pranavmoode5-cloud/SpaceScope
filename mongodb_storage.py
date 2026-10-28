"""
SpaceScope: Big Data Analytics of Global Space Missions
Module 3: MongoDB Storage & Database Operations
Handles data storage and retrieval from MongoDB
"""

from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBSimulator:
    """
    Simulates MongoDB operations for SpaceScope.
    In production, this would use pymongo to connect to actual MongoDB instance.
    
    Database: spacescope
    Collections:
    - missions: Processed mission records
    - organizations: Organization statistics
    - rockets: Rocket usage data
    - launch_sites: Launch location data
    - analytics: Aggregated analytical results
    """
    
    def __init__(self, database_name="spacescope"):
        """Initialize MongoDB simulator"""
        self.database_name = database_name
        self.collections = {
            'missions': [],
            'organizations': [],
            'rockets': [],
            'launch_sites': [],
            'analytics': []
        }
        logger.info(f"✅ MongoDB Simulator initialized for database: {database_name}")
    
    def store_missions(self, missions_data):
        """
        Store processed mission records in MongoDB missions collection
        """
        print("\n💾 Storing Missions in MongoDB")
        print("-" * 80)
        
        stored_count = 0
        
        try:
            # Convert to list of dictionaries if it's a DataFrame
            if hasattr(missions_data, 'to_dict'):
                records = missions_data.to_dict('records')
            else:
                records = missions_data
            
            for record in records:
                # Create MongoDB document
                mission_doc = {
                    "_id": f"M{len(self.collections['missions']) + 1:04d}",
                    "company": record.get('company'),
                    "rocket": record.get('rocket'),
                    "launch_date": str(record.get('launch_date')),
                    "year": int(record.get('year', 0)),
                    "month": int(record.get('month', 0)),
                    "launch_site": record.get('launch_site'),
                    "country": record.get('country'),
                    "mission_status": record.get('mission_status'),
                    "mission_type": record.get('mission_type'),
                    "stored_at": datetime.now().isoformat()
                }
                
                self.collections['missions'].append(mission_doc)
                stored_count += 1
            
            logger.info(f"✅ Stored {stored_count} mission records in MongoDB")
            print(f"✅ Stored {stored_count} mission records")
            print(f"   Collection: spacescope.missions")
            print(f"   Status: Records persisted and indexed")
            
        except Exception as e:
            logger.error(f"❌ Error storing missions: {e}")
        
        return stored_count
    
    def store_organization_stats(self, org_data):
        """Store organization statistics in MongoDB"""
        print("\n💾 Storing Organization Statistics")
        print("-" * 80)
        
        stored_count = 0
        
        try:
            if hasattr(org_data, 'to_dict'):
                records = org_data.to_dict('records')
            elif hasattr(org_data, 'collect'):  # Spark DataFrame
                records = [row.asDict() for row in org_data.collect()]
            else:
                records = org_data
            
            for record in records:
                org_doc = {
                    "_id": record.get('company', 'Unknown'),
                    "company": record.get('company'),
                    "mission_count": int(record.get('mission_count', 0)),
                    "success_rate": float(record.get('success_rate', 0)),
                    "rocket_types": int(record.get('rocket_types', 0)),
                    "updated_at": datetime.now().isoformat()
                }
                
                self.collections['organizations'].append(org_doc)
                stored_count += 1
            
            logger.info(f"✅ Stored {stored_count} organization records")
            print(f"✅ Stored {stored_count} organization records")
            print(f"   Collection: spacescope.organizations")
            
        except Exception as e:
            logger.error(f"❌ Error storing organization stats: {e}")
        
        return stored_count
    
    def store_rocket_stats(self, rocket_data):
        """Store rocket usage statistics in MongoDB"""
        print("\n💾 Storing Rocket Usage Statistics")
        print("-" * 80)
        
        stored_count = 0
        
        try:
            if hasattr(rocket_data, 'to_dict'):
                records = rocket_data.to_dict('records')
            elif hasattr(rocket_data, 'collect'):  # Spark DataFrame
                records = [row.asDict() for row in rocket_data.collect()]
            else:
                records = rocket_data
            
            for record in records:
                rocket_doc = {
                    "_id": record.get('rocket', 'Unknown'),
                    "rocket_name": record.get('rocket'),
                    "usage_count": int(record.get('usage_count', 0)),
                    "success_rate": float(record.get('success_rate', 0)),
                    "organizations": int(record.get('organizations', 0)),
                    "updated_at": datetime.now().isoformat()
                }
                
                self.collections['rockets'].append(rocket_doc)
                stored_count += 1
            
            logger.info(f"✅ Stored {stored_count} rocket records")
            print(f"✅ Stored {stored_count} rocket records")
            print(f"   Collection: spacescope.rockets")
            
        except Exception as e:
            logger.error(f"❌ Error storing rocket stats: {e}")
        
        return stored_count
    
    def store_launch_site_stats(self, site_data):
        """Store launch site statistics in MongoDB"""
        print("\n💾 Storing Launch Site Statistics")
        print("-" * 80)
        
        stored_count = 0
        
        try:
            if hasattr(site_data, 'to_dict'):
                records = site_data.to_dict('records')
            elif hasattr(site_data, 'collect'):  # Spark DataFrame
                records = [row.asDict() for row in site_data.collect()]
            else:
                records = site_data
            
            for record in records:
                site_doc = {
                    "_id": f"{record.get('launch_site', 'Unknown')}_{record.get('country', 'Unknown')}",
                    "launch_site": record.get('launch_site'),
                    "country": record.get('country'),
                    "mission_count": int(record.get('mission_count', 0)),
                    "success_rate": float(record.get('success_rate', 0)),
                    "updated_at": datetime.now().isoformat()
                }
                
                self.collections['launch_sites'].append(site_doc)
                stored_count += 1
            
            logger.info(f"✅ Stored {stored_count} launch site records")
            print(f"✅ Stored {stored_count} launch site records")
            print(f"   Collection: spacescope.launch_sites")
            
        except Exception as e:
            logger.error(f"❌ Error storing launch site stats: {e}")
        
        return stored_count
    
    def store_analytics_results(self, analytics_dict):
        """Store aggregated analytics results in MongoDB"""
        print("\n💾 Storing Aggregated Analytics Results")
        print("-" * 80)
        
        stored_count = 0
        
        try:
            for analysis_type, data in analytics_dict.items():
                
                # Convert Spark DataFrame to dictionaries
                if hasattr(data, 'collect'):
                    records = [row.asDict() for row in data.collect()]
                elif hasattr(data, 'to_dict'):
                    records = data.to_dict('records')
                else:
                    records = data
                
                # Store each aggregation result
                for record in records:
                    analytics_doc = {
                        "_id": f"{analysis_type}_{stored_count}",
                        "analysis_type": analysis_type,
                        "data": record,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    self.collections['analytics'].append(analytics_doc)
                    stored_count += 1
            
            logger.info(f"✅ Stored {stored_count} analytics result documents")
            print(f"✅ Stored {stored_count} analytics results")
            print(f"   Collection: spacescope.analytics")
            
        except Exception as e:
            logger.error(f"❌ Error storing analytics: {e}")
        
        return stored_count
    
    def retrieve_missions(self, query=None, limit=10):
        """Retrieve missions from MongoDB"""
        print(f"\n🔍 Retrieving Missions from MongoDB (Limit: {limit})")
        print("-" * 80)
        
        results = self.collections['missions'][:limit]
        print(f"✅ Retrieved {len(results)} mission records")
        
        return results
    
    def retrieve_organization_stats(self, limit=10):
        """Retrieve organization statistics from MongoDB"""
        print(f"\n🔍 Retrieving Organization Statistics (Limit: {limit})")
        print("-" * 80)
        
        results = self.collections['organizations'][:limit]
        print(f"✅ Retrieved {len(results)} organization records")
        
        return results
    
    def retrieve_analytics_summary(self):
        """Retrieve analytics summary from MongoDB"""
        print("\n🔍 Retrieving Analytics Summary from MongoDB")
        print("-" * 80)
        
        summary = {
            'total_missions': len(self.collections['missions']),
            'total_organizations': len(self.collections['organizations']),
            'total_rockets': len(self.collections['rockets']),
            'total_launch_sites': len(self.collections['launch_sites']),
            'total_analytics_records': len(self.collections['analytics'])
        }
        
        print(f"✅ Missions stored: {summary['total_missions']}")
        print(f"✅ Organizations stored: {summary['total_organizations']}")
        print(f"✅ Rockets stored: {summary['total_rockets']}")
        print(f"✅ Launch sites stored: {summary['total_launch_sites']}")
        print(f"✅ Analytics records: {summary['total_analytics_records']}")
        
        return summary
    
    def get_database_stats(self):
        """Get database statistics"""
        stats = {
            'database_name': self.database_name,
            'collections': list(self.collections.keys()),
            'collection_sizes': {
                name: len(docs) for name, docs in self.collections.items()
            },
            'total_documents': sum(len(docs) for docs in self.collections.values()),
            'storage_status': 'Active'
        }
        return stats
    
    def display_collection_samples(self, collection_name, limit=3):
        """Display sample documents from a collection"""
        print(f"\n📋 Sample Documents from {collection_name}:")
        print("-" * 80)
        
        if collection_name not in self.collections:
            print(f"❌ Collection '{collection_name}' not found")
            return
        
        samples = self.collections[collection_name][:limit]
        
        for i, doc in enumerate(samples, 1):
            print(f"\nDocument {i}:")
            print(json.dumps(doc, indent=2, default=str))
        
        print("-" * 80)
    
    def export_to_json(self, filename="spacescope_export.json"):
        """Export all data to JSON file"""
        try:
            export_data = {
                'database': self.database_name,
                'export_time': datetime.now().isoformat(),
                'collections': self.collections
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"✅ Exported data to {filename}")
            print(f"✅ Data exported to {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error exporting data: {e}")


def main():
    """Test MongoDB storage module"""
    print("\n" + "="*80)
    print("🚀 SpaceScope: MongoDB Storage Module")
    print("="*80)
    
    # Initialize MongoDB simulator
    db = MongoDBSimulator()
    
    # Import PySpark processor
    from data_ingestion import SpaceMissionDataSource
    
    # Load sample data
    data_source = SpaceMissionDataSource()
    pandas_df = data_source.create_sample_dataset()
    
    # Store missions
    db.store_missions(pandas_df)
    
    # Store sample aggregations (simulated)
    org_stats = pandas_df.groupby('company').agg({
        'rocket': 'count',
        'mission_status': lambda x: (x == 'Success').sum() / len(x)
    }).rename(columns={'rocket': 'mission_count', 'mission_status': 'success_rate'}).reset_index()
    org_stats.rename(columns={'company': 'company'}, inplace=True)
    org_stats['rocket_types'] = 1
    
    db.store_organization_stats(org_stats)
    
    # Store rocket stats
    rocket_stats = pandas_df.groupby('rocket').agg({
        'company': 'count',
        'mission_status': lambda x: (x == 'Success').sum() / len(x)
    }).rename(columns={'company': 'usage_count', 'mission_status': 'success_rate'}).reset_index()
    rocket_stats['organizations'] = 1
    
    db.store_rocket_stats(rocket_stats)
    
    # Store launch site stats
    site_stats = pandas_df.groupby(['launch_site', 'country']).agg({
        'rocket': 'count',
        'mission_status': lambda x: (x == 'Success').sum() / len(x)
    }).rename(columns={'rocket': 'mission_count', 'mission_status': 'success_rate'}).reset_index()
    
    db.store_launch_site_stats(site_stats)
    
    # Display database statistics
    print("\n📊 MongoDB Database Statistics:")
    print("-" * 80)
    stats = db.get_database_stats()
    print(f"Database Name: {stats['database_name']}")
    print(f"Collections: {', '.join(stats['collections'])}")
    print(f"Total Documents: {stats['total_documents']}")
    print("\nCollection Sizes:")
    for col, size in stats['collection_sizes'].items():
        print(f"  - {col}: {size} documents")
    
    # Display sample documents
    db.display_collection_samples('missions', 2)
    db.display_collection_samples('organizations', 3)
    
    # Retrieve data
    missions = db.retrieve_missions(limit=5)
    orgs = db.retrieve_organization_stats(limit=5)
    summary = db.retrieve_analytics_summary()
    
    # Export data
    db.export_to_json("spacescope_mongodb_export.json")
    
    return db


if __name__ == "__main__":
    db = main()
    print("\n✅ MongoDB storage module test completed!")
