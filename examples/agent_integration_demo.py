#!/usr/bin/env python3
"""
Comprehensive Agent Integration Demo

This example demonstrates how all the agents work together in a realistic
lead management workflow:

1. EmailQualifier - Qualifies incoming leads
2. ReplyAnalyzer - Analyzes email replies from leads
3. MeetingScheduler - Handles meeting scheduling requests
4. AgentCore - Provides the foundation for all agents

The demo simulates a complete lead lifecycle from initial contact through
meeting scheduling.
"""

from datetime import datetime
from typing import Dict, Any

# Import our agents
from agents.agent_core import AgentCore
from agents.email_qualifier import EmailQualifier
from agents.reply_analyzer import ReplyAnalyzer
from agents.meeting_scheduler import MeetingScheduler
from core.memory_manager import MemoryManager


class LeadManagementDemo:
    """Demonstrates integrated agent functionality."""
    
    def __init__(self):
        """Initialize the demo with all agents."""
        # Initialize core components
        self.memory_manager = MemoryManager()
        self.agent_core = AgentCore()
        
        # Initialize specialized agents
        self.email_qualifier = EmailQualifier(self.agent_core, self.memory_manager)
        self.reply_analyzer = ReplyAnalyzer(self.agent_core, self.memory_manager)
        self.meeting_scheduler = MeetingScheduler(self.agent_core, self.memory_manager)
        
        print("🚀 Lead Management System Initialized")
        print("=" * 50)
    
    def run_demo(self):
        """Run the complete integration demo."""
        print("\n📧 DEMO: Complete Lead Management Workflow")
        print("=" * 50)
        
        # Step 1: Qualify a new lead
        print("\n1️⃣ STEP 1: Lead Qualification")
        print("-" * 30)
        lead_data = self._get_sample_lead_data()
        qualification_result = self._demonstrate_lead_qualification(lead_data)
        
        # Step 2: Analyze a reply from the lead
        print("\n2️⃣ STEP 2: Reply Analysis")
        print("-" * 30)
        reply_data = self._get_sample_reply_data()
        reply_analysis = self._demonstrate_reply_analysis(reply_data, lead_data)
        
        # Step 3: Handle meeting scheduling request
        print("\n3️⃣ STEP 3: Meeting Scheduling")
        print("-" * 30)
        meeting_request = self._get_sample_meeting_request()
        meeting_result = self._demonstrate_meeting_scheduling(meeting_request, lead_data)
        
        # Step 4: Show integrated workflow
        print("\n4️⃣ STEP 4: Integrated Workflow Summary")
        print("-" * 30)
        self._demonstrate_integrated_workflow(qualification_result, reply_analysis, meeting_result)
        
        print("\n✅ Demo completed successfully!")
        print("=" * 50)
    
    def _get_sample_lead_data(self) -> Dict[str, Any]:
        """Get sample lead data for qualification."""
        return {
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@techcorp.com',
            'company': 'TechCorp Solutions',
            'message_content': '''Hi there,
            
            I'm the VP of Engineering at TechCorp Solutions, a 200-person software company.
            We're looking for a solution to help us manage our growing customer base more effectively.
            
            Our current system is becoming a bottleneck, and we need something that can scale
            with our rapid growth. We have a budget of around $50K annually for the right solution.
            
            Could you tell me more about your platform and how it might help us?
            
            Best regards,
            Sarah Johnson
            VP of Engineering, TechCorp Solutions''',
            'company_size': '200',
            'industry': 'Software',
            'lead_source': 'Website Contact Form'
        }
    
    def _get_sample_reply_data(self) -> Dict[str, Any]:
        """Get sample reply data for analysis."""
        return {
            'reply_text': '''Thanks for the detailed information about your platform!
            
            This looks very promising. I'd like to schedule a demo to see how it would work
            with our current setup. I'm particularly interested in the integration capabilities
            and scalability features you mentioned.
            
            I'm available next week for a 30-minute demo. Tuesday or Wednesday afternoon
            would work best for me. Could we set something up?
            
            Also, could you send me some case studies of similar companies that have
            implemented your solution?
            
            Looking forward to hearing from you.
            
            Sarah''',
            'sender_email': 'sarah.johnson@techcorp.com',
            'subject': 'Re: TechCorp Solutions - Platform Demo Request',
            'timestamp': datetime.now().isoformat(),
            'lead_id': 'lead_sarah_johnson'
        }
    
    def _get_sample_meeting_request(self) -> Dict[str, Any]:
        """Get sample meeting request data."""
        return {
            'request_text': '''Hi,
            
            Following up on our email conversation. I'd like to schedule that demo we discussed.
            I'm available Tuesday or Wednesday afternoon next week, preferably between 2-4 PM EST.
            
            The demo should cover:
            - Integration with our existing CRM
            - Scalability for 200+ users
            - Pricing options
            
            Please let me know what works for your schedule.
            
            Thanks,
            Sarah''',
            'sender_email': 'sarah.johnson@techcorp.com',
            'preferred_times': 'Tuesday or Wednesday afternoon, 2-4 PM EST',
            'meeting_type': 'demo',
            'lead_id': 'lead_sarah_johnson'
        }
    
    def _demonstrate_lead_qualification(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate lead qualification process."""
        try:
            print(f"📋 Qualifying lead: {lead_data['name']} from {lead_data['company']}")
            
            # Qualify the lead
            qualification_result = self.email_qualifier.qualify(lead_data)
            
            print("✅ Qualification completed!")
            print(f"   • Score: {qualification_result.get('score', 'N/A')}/100")
            print(f"   • Priority: {qualification_result.get('priority', 'N/A')}")
            print(f"   • Budget Signals: {qualification_result.get('budget_signals', 'N/A')}")
            print(f"   • Decision Authority: {qualification_result.get('decision_authority', 'N/A')}")
            print(f"   • Next Action: {qualification_result.get('next_action', 'N/A')}")
            
            return qualification_result
            
        except Exception as e:
            print(f"❌ Qualification failed: {str(e)}")
            return {}
    
    def _demonstrate_reply_analysis(self, reply_data: Dict[str, Any], lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate reply analysis process."""
        try:
            print(f"📨 Analyzing reply from: {reply_data['sender_email']}")
            
            # Analyze the reply
            analysis_result = self.reply_analyzer.analyze(reply_data, lead_context)
            
            print("✅ Reply analysis completed!")
            print(f"   • Intent: {analysis_result.get('intent', 'N/A')}")
            print(f"   • Sentiment: {analysis_result.get('sentiment', 'N/A')}")
            print(f"   • Engagement Level: {analysis_result.get('engagement_level', 'N/A')}")
            print(f"   • Urgency: {analysis_result.get('urgency', 'N/A')}")
            print(f"   • Next Action: {analysis_result.get('next_action', 'N/A')}")
            
            # Calculate updated score
            new_score = self.reply_analyzer.calculate_score(analysis_result)
            print(f"   • Updated Lead Score: {new_score}")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Reply analysis failed: {str(e)}")
            return {}
    
    def _demonstrate_meeting_scheduling(self, request_data: Dict[str, Any], lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate meeting scheduling process."""
        try:
            print(f"📅 Processing meeting request from: {request_data['sender_email']}")
            
            # Analyze the meeting request
            analysis_result = self.meeting_scheduler.analyze_request(request_data, lead_context)
            print("✅ Meeting request analyzed!")
            print(f"   • Intent: {analysis_result.get('intent', 'N/A')}")
            print(f"   • Meeting Type: {analysis_result.get('meeting_type', 'N/A')}")
            print(f"   • Urgency: {analysis_result.get('urgency', 'N/A')}")
            
            # Propose meeting times
            preferences = {
                'preferred_days': ['Tuesday', 'Wednesday'],
                'preferred_times': ['14:00-16:00'],
                'urgency': analysis_result.get('urgency', 'medium')
            }
            
            proposed_times = self.meeting_scheduler.propose_meeting_times(preferences, 3)
            print(f"✅ Proposed {len(proposed_times)} meeting times:")
            
            for i, proposal in enumerate(proposed_times, 1):
                print(f"   {i}. {proposal.get('formatted_time', 'N/A')} (Score: {proposal.get('score', 'N/A')})")
            
            # Generate response
            response = self.meeting_scheduler.generate_meeting_response(analysis_result, proposed_times)
            print("✅ Generated meeting response:")
            print(f"   {response[:100]}...")
            
            # Book the first available time (simulate user selection)
            if proposed_times:
                meeting_data = {
                    'lead_id': request_data['lead_id'],
                    'start_time': proposed_times[0]['start_time'],
                    'duration': 30,
                    'meeting_type': analysis_result.get('meeting_type', 'demo')
                }
                
                booking_result = self.meeting_scheduler.book(meeting_data)
                print(f"✅ Meeting booking: {booking_result.get('status', 'N/A')}")
                if booking_result.get('booking_id'):
                    print(f"   • Booking ID: {booking_result['booking_id']}")
            
            return {
                'analysis': analysis_result,
                'proposed_times': proposed_times,
                'response': response
            }
            
        except Exception as e:
            print(f"❌ Meeting scheduling failed: {str(e)}")
            return {}
    
    def _demonstrate_integrated_workflow(self, qualification: Dict, reply_analysis: Dict, meeting_result: Dict):
        """Show how all the results work together."""
        print("🔄 Integrated Workflow Summary:")
        print()
        
        # Lead journey
        print("📈 Lead Journey:")
        print(f"   1. Initial qualification score: {qualification.get('score', 'N/A')}")
        print(f"   2. Reply engagement level: {reply_analysis.get('engagement_level', 'N/A')}")
        print(f"   3. Meeting request intent: {meeting_result.get('analysis', {}).get('intent', 'N/A')}")
        
        # Priority escalation
        initial_priority = qualification.get('priority', 'medium')
        reply_urgency = reply_analysis.get('urgency', 'medium')
        meeting_urgency = meeting_result.get('analysis', {}).get('urgency', 'medium')
        
        print()
        print("🚨 Priority Escalation:")
        print(f"   • Initial: {initial_priority}")
        print(f"   • After reply: {reply_urgency}")
        print(f"   • Meeting urgency: {meeting_urgency}")
        
        # Next actions
        print()
        print("📋 Recommended Actions:")
        actions = []
        
        if qualification.get('score', 0) > 70:
            actions.append("High-priority lead - assign to senior sales rep")
        
        if reply_analysis.get('engagement_level') == 'high':
            actions.append("Lead is highly engaged - prioritize response")
        
        if meeting_result.get('analysis', {}).get('intent') == 'schedule_meeting':
            actions.append("Meeting requested - send calendar invite")
        
        for i, action in enumerate(actions, 1):
            print(f"   {i}. {action}")
        
        # Memory integration
        print()
        print("🧠 Memory Integration:")
        print("   • Lead qualification stored for future reference")
        print("   • Reply analysis added to lead history")
        print("   • Meeting preferences saved for follow-ups")
        print("   • All interactions linked for complete context")


def main():
    """Run the integration demo."""
    try:
        demo = LeadManagementDemo()
        demo.run_demo()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 