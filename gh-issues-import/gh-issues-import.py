#!/usr/bin/env python

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import urllib2
import json
from StringIO import StringIO
import base64
import pprint

#==== configurations =======
username = "user@example.com"
password = "naked_password"
src_repo = "octocat/Hello-World"
dst_repo = "helloworld-inc/Hello-World"
#==== end of configurations ===

server = "api.github.com"
src_url = "https://%s/repos/%s" % (server, src_repo)
dst_url = "https://%s/repos/%s" % (server, dst_repo)

def request(logging_context, url, body=None):
  if body:
    print "Request[%s]: %s w/ body=%s" % (logging_context, url, body)
  else :
    print "Request[%s]: %s" % (logging_context, url)
  req = urllib2.Request(url, body)
  req.add_header("Authorization", "Basic " + base64.urlsafe_b64encode("%s:%s" % (username, password)))
  req.add_header("Content-Type", "application/json")
  req.add_header("Accept", "application/json")
  return urllib2.urlopen(req)

def get_milestones(url):
  response = request('get_milestones', "%s/milestones?state=open" % url)
  result = response.read()
  milestones = json.load(StringIO(result))
  return milestones

def get_labels(url):
  response = request('get_labels', "%s/labels" % url)
  result = response.read()
  labels = json.load(StringIO(result))
  return labels

def get_issues(url):
  response = request('get_issues', "%s/issues?filter=all" % url)
  result = response.read()
  open_issues = json.load(StringIO(result))

  response = request('get_issues', "%s/issues?state=closed&filter=all" % url)
  result = response.read()
  closed_issues = json.load(StringIO(result))

  issues = open_issues + closed_issues
  return issues

def get_comments_on_issue(issue):
  if issue.has_key("comments") \
    and issue["comments"] is not None \
    and issue["comments"] != 0:
    response = request('get_comments_on_issue', "%s/comments" % issue["url"])
    result = response.read()
    comments = json.load(StringIO(result))
    return comments
  else :
    return []

def import_milestones(milestones):
  for source in milestones:
    dest = json.dumps({
      "title": source["title"],
      "state": "open",
      "description": source["description"],
      "due_on": source["due_on"]})

    res = request('import_milestones', "%s/milestones" % dst_url, dest)
    data = res.read()
    res_milestone = json.load(StringIO(data))
    print "Successfully created milestone %s" % res_milestone["title"]

def import_labels(labels):
  for source in labels:
    dest = json.dumps({
      "name": source["name"],
      "color": source["color"]
    })

    res = request('import_labels', "%s/labels" % dst_url, dest)
    data = res.read()
    res_label = json.load(StringIO(data))
    print "Successfully created label %s" % res_label["name"]

def import_issues(issues, dst_milestones, dst_labels):
  for source in issues:
    labels = []
    if source.has_key("labels"):
      for src_label in source["labels"]:
        name = src_label["name"]
        for dst_label in dst_labels:
          if dst_label["name"] == name:
            labels.append(name)
            break

    milestone = None
    if source.has_key("milestone") and source["milestone"] is not None:
      title = source["milestone"]["title"]
      for dst_milestone in dst_milestones:
        if dst_milestone["title"] == title:
          milestone = dst_milestone["number"]
          break

    assignee = None
    if source.has_key("assignee") and source["assignee"] is not None:
      assignee = source["assignee"]["login"]

    body = None
    if source.has_key("body") and source["body"] is not None:
      body = source["body"]

    dest = json.dumps({
      "title": source["title"],
      "body": body,
      "assignee": assignee,
      "milestone": milestone,
      "labels": labels
    })

    res = request('import_issues', "%s/issues" % dst_url, dest)
    data = res.read()
    res_issue = json.load(StringIO(data))
    print "Successfully created issue %s" % res_issue["title"]

    # Handle issue comments
    comments = get_comments_on_issue(source)

    for comment in comments:
      dest = json.dumps({
        "body": comment["body"]
      })
      res = request('import_issues', "%s/comments" % (res_issue["url"]), dest)
      data = res.read()
      res_cmt = json.load(StringIO(data))
      print "Successfully created comment %s on issue %s" % (res_cmt["body"], res_issue["id"])

def main():
  #get milestones and issues to import
  milestones = get_milestones(src_url)
  labels = get_labels(src_url)

  #do import
  import_milestones(milestones)
  import_labels(labels)

  #get imported milestones and labels
  milestones = get_milestones(dst_url)
  labels = get_labels(dst_url)

  #process issues
  issues = get_issues(src_url)
  import_issues(issues, milestones, labels)


if __name__ == '__main__':
  main()
