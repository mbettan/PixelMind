class JiraReporter:
    @staticmethod
    def convert_to_adf(summary: str, description: str, severity: str = "Medium"):
        """
        Translates raw JSON reports into Atlassian Document Format (ADF) for Jira.
        """
        adf = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": f"Defect Report: {summary}"}]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Severity: ", "marks": [{"type": "strong"}]},
                        {"type": "text", "text": severity}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description}]
                }
            ]
        }
        return adf

    def report_defect(self, adf_content: dict):
        """
        Autonomous Defect Reporting. In a real scenario, this would call the Jira API via MCP.
        """
        print("Reporting defect to Jira...")
        # print(json.dumps(adf_content, indent=2))
        return True
