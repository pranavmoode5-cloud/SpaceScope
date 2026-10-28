"""
SpaceScope: Big Data Analytics of Global Space Missions
Module 4: Analytics & Reporting
Performs analytical queries and generates reports
"""

import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpaceAnalytics:
    """
    Performs analytics and generates reports on space mission data
    6 Analytics Modules:
    1. Temporal Analysis (Year trends)
    2. Organization Analysis
    3. Rocket Analysis
    4. Mission Type Analysis
    5. Launch Site Analysis
    6. Mission Outcome Analysis
    """
    
    def __init__(self, missions_df):
        """Initialize analytics with missions data"""
        self.missions_df = missions_df
        self.reports = {}
        logger.info("✅ Analytics module initialized")
    
    def module_1_temporal_analysis(self):
        """
        MODULE 1: TEMPORAL ANALYSIS
        Questions: How many missions per year? Which years had high activity?
        How has launch activity changed over time?
        """
        print("\n" + "="*80)
        print("📅 MODULE 1: TEMPORAL ANALYSIS - Launch Trends Over Time")
        print("="*80)
        
        # Group by year
        yearly_stats = self.missions_df.groupby('year').agg({
            'rocket': 'count',
            'mission_status': [
                lambda x: (x == 'Success').sum(),
                lambda x: (x == 'Failed').sum(),
                lambda x: (x != 'Success').sum()
            ]
        }).round(2)
        
        yearly_stats.columns = ['total_missions', 'successful', 'failed', 'other']
        yearly_stats['success_rate'] = (yearly_stats['successful'] / yearly_stats['total_missions'] * 100).round(1)
        
        print("\n📊 Missions by Year:")
        print(yearly_stats.to_string())
        
        # Key insights
        peak_year = yearly_stats['total_missions'].idxmax()
        peak_count = yearly_stats.loc[peak_year, 'total_missions']
        
        print(f"\n🔍 Key Insights:")
        print(f"   Peak Year: {int(peak_year)} with {int(peak_count)} missions")
        print(f"   Overall Success Rate: {(yearly_stats['successful'].sum() / yearly_stats['total_missions'].sum() * 100):.1f}%")
        print(f"   Year Range: {int(yearly_stats.index.min())} - {int(yearly_stats.index.max())}")
        
        self.reports['temporal'] = yearly_stats
        return yearly_stats
    
    def module_2_organization_analysis(self):
        """
        MODULE 2: ORGANIZATION ANALYSIS
        Questions: Missions per organization? Organization activity over time?
        Mission outcomes by organization?
        """
        print("\n" + "="*80)
        print("🏢 MODULE 2: ORGANIZATION ANALYSIS - Space Agency Performance")
        print("="*80)
        
        org_stats = self.missions_df.groupby('company').agg({
            'rocket': 'count',
            'mission_status': [
                lambda x: (x == 'Success').sum(),
                lambda x: (x == 'Failed').sum()
            ],
            'country': 'first'
        }).round(2)
        
        org_stats.columns = ['total_missions', 'successful', 'failed', 'country']
        org_stats['success_rate'] = (org_stats['successful'] / org_stats['total_missions'] * 100).round(1)
        org_stats = org_stats.sort_values('total_missions', ascending=False)
        
        print("\n📊 Top Organizations by Mission Count:")
        print(org_stats[['total_missions', 'successful', 'failed', 'success_rate', 'country']].head(10).to_string())
        
        print(f"\n🔍 Key Insights:")
        print(f"   Total Unique Organizations: {len(org_stats)}")
        print(f"   Top Organization: {org_stats.index[0]} ({int(org_stats.iloc[0]['total_missions'])} missions)")
        print(f"   Most Successful: {org_stats['success_rate'].idxmax()} ({org_stats['success_rate'].max():.1f}% success)")
        
        self.reports['organizations'] = org_stats
        return org_stats
    
    def module_3_rocket_analysis(self):
        """
        MODULE 3: ROCKET ANALYSIS
        Questions: Most frequently used rockets? Rocket usage over time?
        Rocket success/failure distribution?
        """
        print("\n" + "="*80)
        print("🚀 MODULE 3: ROCKET ANALYSIS - Launch Vehicle Performance")
        print("="*80)
        
        rocket_stats = self.missions_df.groupby('rocket').agg({
            'company': 'count',
            'mission_status': [
                lambda x: (x == 'Success').sum(),
                lambda x: (x == 'Failed').sum()
            ]
        }).round(2)
        
        rocket_stats.columns = ['usage_count', 'successful', 'failed']
        rocket_stats['success_rate'] = (rocket_stats['successful'] / rocket_stats['usage_count'] * 100).round(1)
        rocket_stats = rocket_stats.sort_values('usage_count', ascending=False)
        
        print("\n📊 Top Rockets by Usage:")
        print(rocket_stats.head(15).to_string())
        
        print(f"\n🔍 Key Insights:")
        print(f"   Total Unique Rockets: {len(rocket_stats)}")
        print(f"   Most Used Rocket: {rocket_stats.index[0]} ({int(rocket_stats.iloc[0]['usage_count'])} launches)")
        print(f"   Most Reliable: {rocket_stats['success_rate'].idxmax()} ({rocket_stats['success_rate'].max():.1f}% success)")
        
        self.reports['rockets'] = rocket_stats
        return rocket_stats
    
    def module_4_mission_type_analysis(self):
        """
        MODULE 4: MISSION TYPE ANALYSIS
        Categories: Communication, Earth Observation, Navigation, 
        Scientific Research, Exploration, Crewed Missions
        """
        print("\n" + "="*80)
        print("🎯 MODULE 4: MISSION TYPE ANALYSIS - Mission Categories")
        print("="*80)
        
        mission_type_stats = self.missions_df.groupby('mission_type').agg({
            'rocket': 'count',
            'mission_status': [
                lambda x: (x == 'Success').sum(),
                lambda x: (x == 'Failed').sum()
            ]
        }).round(2)
        
        mission_type_stats.columns = ['count', 'successful', 'failed']
        mission_type_stats['success_rate'] = (mission_type_stats['successful'] / mission_type_stats['count'] * 100).round(1)
        mission_type_stats['percentage'] = (mission_type_stats['count'] / mission_type_stats['count'].sum() * 100).round(1)
        mission_type_stats = mission_type_stats.sort_values('count', ascending=False)
        
        print("\n📊 Mission Type Distribution:")
        print(mission_type_stats.to_string())
        
        print(f"\n🔍 Key Insights:")
        print(f"   Most Common Type: {mission_type_stats.index[0]} ({int(mission_type_stats.iloc[0]['count'])} missions)")
        print(f"   Total Mission Types: {len(mission_type_stats)}")
        for mission_type in mission_type_stats.index[:3]:
            pct = mission_type_stats.loc[mission_type, 'percentage']
            print(f"   - {mission_type}: {pct:.1f}%")
        
        self.reports['mission_types'] = mission_type_stats
        return mission_type_stats
    
    def module_5_launch_site_analysis(self):
        """
        MODULE 5: LAUNCH SITE ANALYSIS
        Questions: Most active launch sites? Country-wise launch activity?
        Launch site trends over time?
        """
        print("\n" + "="*80)
        print("📍 MODULE 5: LAUNCH SITE ANALYSIS - Geographical Distribution")
        print("="*80)
        
        # By launch site
        site_stats = self.missions_df.groupby(['launch_site', 'country']).agg({
            'rocket': 'count',
            'mission_status': [
                lambda x: (x == 'Success').sum(),
                lambda x: (x == 'Failed').sum()
            ]
        }).round(2)
        
        site_stats.columns = ['mission_count', 'successful', 'failed']
        site_stats['success_rate'] = (site_stats['successful'] / site_stats['mission_count'] * 100).round(1)
        site_stats = site_stats.sort_values('mission_count', ascending=False)
        
        print("\n📊 Top Launch Sites:")
        print(site_stats.head(10).to_string())
        
        # By country
        country_stats = self.missions_df.groupby('country').agg({
            'rocket': 'count',
            'mission_status': lambda x: (x == 'Success').sum()
        }).round(2)
        
        country_stats.columns = ['total_missions', 'successful']
        country_stats['success_rate'] = (country_stats['successful'] / country_stats['total_missions'] * 100).round(1)
        country_stats = country_stats.sort_values('total_missions', ascending=False)
        
        print("\n📊 Missions by Country:")
        print(country_stats.head(10).to_string())
        
        print(f"\n🔍 Key Insights:")
        print(f"   Top Launch Site: {site_stats.index[0][0]} ({int(site_stats.iloc[0]['mission_count'])} missions)")
        print(f"   Top Country: {country_stats.index[0]} ({int(country_stats.iloc[0]['total_missions'])} missions)")
        print(f"   Total Countries: {len(country_stats)}")
        
        self.reports['launch_sites'] = site_stats
        self.reports['countries'] = country_stats
        return site_stats, country_stats
    
    def module_6_mission_outcome_analysis(self):
        """
        MODULE 6: MISSION OUTCOME ANALYSIS
        Categories: Successful, Failed, Partial/Other, Unknown
        """
        print("\n" + "="*80)
        print("✅ MODULE 6: MISSION OUTCOME ANALYSIS - Success vs Failure")
        print("="*80)
        
        outcome_stats = self.missions_df['mission_status'].value_counts()
        outcome_pct = (outcome_stats / len(self.missions_df) * 100).round(1)
        
        print("\n📊 Mission Outcome Distribution:")
        outcome_df = pd.DataFrame({
            'Count': outcome_stats,
            'Percentage': outcome_pct
        })
        print(outcome_df.to_string())
        
        # Success rate by company
        company_success = self.missions_df.groupby('company').agg({
            'mission_status': lambda x: (x == 'Success').sum() / len(x) * 100
        }).round(1).sort_values('mission_status', ascending=False)
        company_success.columns = ['success_rate']
        
        print("\n📊 Success Rate by Organization:")
        print(company_success.head(10).to_string())
        
        print(f"\n🔍 Key Insights:")
        successful = (self.missions_df['mission_status'] == 'Success').sum()
        failed = (self.missions_df['mission_status'] == 'Failed').sum()
        partial = len(self.missions_df) - successful - failed
        
        print(f"   Total Missions: {len(self.missions_df)}")
        print(f"   Successful: {successful} ({successful/len(self.missions_df)*100:.1f}%)")
        print(f"   Failed: {failed} ({failed/len(self.missions_df)*100:.1f}%)")
        print(f"   Partial/Other: {partial} ({partial/len(self.missions_df)*100:.1f}%)")
        print(f"   Overall Success Rate: {successful/len(self.missions_df)*100:.1f}%")
        
        self.reports['outcomes'] = outcome_df
        return outcome_df
    
    def generate_comprehensive_report(self):
        """Generate comprehensive analytics report"""
        print("\n" + "="*80)
        print("📑 COMPREHENSIVE ANALYTICS REPORT")
        print("="*80)
        
        # Run all modules
        self.module_1_temporal_analysis()
        self.module_2_organization_analysis()
        self.module_3_rocket_analysis()
        self.module_4_mission_type_analysis()
        self.module_5_launch_site_analysis()
        self.module_6_mission_outcome_analysis()
        
        # Summary
        print("\n" + "="*80)
        print("📊 EXECUTIVE SUMMARY")
        print("="*80)
        
        print(f"\n🎯 Global Space Mission Statistics:")
        print(f"   Total Missions Analyzed: {len(self.missions_df)}")
        print(f"   Year Range: 1957 - 2022")
        print(f"   Unique Organizations: {self.missions_df['company'].nunique()}")
        print(f"   Unique Rockets: {self.missions_df['rocket'].nunique()}")
        print(f"   Unique Launch Sites: {self.missions_df['launch_site'].nunique()}")
        print(f"   Countries Involved: {self.missions_df['country'].nunique()}")
        
        success_rate = (self.missions_df['mission_status'] == 'Success').sum() / len(self.missions_df) * 100
        print(f"\n📈 Overall Performance:")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Most Active Organization: {self.missions_df['company'].value_counts().index[0]}")
        print(f"   Most Used Rocket: {self.missions_df['rocket'].value_counts().index[0]}")
        print(f"   Most Common Mission Type: {self.missions_df['mission_type'].value_counts().index[0]}")
        
        self.reports['summary'] = {
            'total_missions': len(self.missions_df),
            'success_rate': success_rate,
            'unique_organizations': self.missions_df['company'].nunique(),
            'unique_rockets': self.missions_df['rocket'].nunique(),
            'year_range': f"{int(self.missions_df['year'].min())} - {int(self.missions_df['year'].max())}"
        }
        
        return self.reports
    
    def export_reports(self, filename="spacescope_analytics_report.txt"):
        """Export reports to file"""
        try:
            with open(filename, 'w') as f:
                f.write("="*80 + "\n")
                f.write("SPACESCOPE: BIG DATA ANALYTICS OF GLOBAL SPACE MISSIONS\n")
                f.write("="*80 + "\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for report_name, report_data in self.reports.items():
                    f.write(f"\n{'='*80}\n")
                    f.write(f"Report: {report_name.upper()}\n")
                    f.write(f"{'='*80}\n\n")
                    
                    if isinstance(report_data, pd.DataFrame):
                        f.write(report_data.to_string())
                    elif isinstance(report_data, dict):
                        for key, value in report_data.items():
                            f.write(f"{key}: {value}\n")
                    else:
                        f.write(str(report_data))
                    
                    f.write("\n\n")
            
            logger.info(f"✅ Reports exported to {filename}")
            print(f"✅ Reports exported to {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error exporting reports: {e}")


def main():
    """Test analytics module"""
    print("\n" + "="*80)
    print("🚀 SpaceScope: Analytics & Reporting Module")
    print("="*80)
    
    from data_ingestion import SpaceMissionDataSource
    
    # Load data
    data_source = SpaceMissionDataSource()
    missions_df = data_source.create_sample_dataset()
    
    # Initialize analytics
    analytics = SpaceAnalytics(missions_df)
    
    # Generate comprehensive report
    reports = analytics.generate_comprehensive_report()
    
    # Export reports
    analytics.export_reports()
    
    return analytics, reports


if __name__ == "__main__":
    analytics, reports = main()
    print("\n✅ Analytics module completed!")
