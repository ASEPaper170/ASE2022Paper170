Kubernetes commit hash changed to

commit 04b8cec5c32bc23aaf9629d60c9ae76fe3629c71
Author: Jordan Liggitt <liggitt@google.com>
Date:   Thu Apr 22 11:12:54 2021 -0400

from

commit 97d40890d00acf721ecabb8c9a6fec3b3234b74b
Merge: 15a8a8ec4a3 7c99f426cd0
Author: Kubernetes Prow Robot <k8s-ci-robot@users.noreply.github.com>
Date:   Sun Feb 7 17:53:11 2021 -0800

because the go.mod file is invalid between these commits, making the go tool fail the list operation.
