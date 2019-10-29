

class DB:
  def __init__(self):
    self.table=[]

  def newReport(self, userId):
    self.table.append({"userId":userId})
    return len(self.table)-1

  def getReport(self, reportId):
    return self.table[reportId]
